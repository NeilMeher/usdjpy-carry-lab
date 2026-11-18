import argparse
from bisect import bisect_right
import csv
from datetime import date, timedelta
from hashlib import sha256
import json
from math import log
from pathlib import Path
from subprocess import run

import numpy as np
from figure import Plot

ROOT = Path(__file__).resolve().parent
SERIES = ("DEXJPUS","DFF","IRSTCI01JPM156N")
YEARS = (date(2003,10,1),date(2024,12,31))
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
OPEN_EXIT = .0001
LEV = (3,8,15,25)
COSTS = (0,50,150)
SEED = 202405


def read_data(folder, download):
    if download:
        folder.mkdir(parents=True,exist_ok=True)
        for key in SERIES:
            response = run(["curl", "--fail", "--silent", "--show-error", "--location",
                            "--max-time", "30", URL+key], check=True, capture_output=True)
            (folder/(key+".csv")).write_bytes(response.stdout)
    outputs, hashes = [], {}
    for key in SERIES:
        with (folder/(key+".csv")).open(newline="",encoding="utf-8-sig") as file:
            table = {}
            for row in csv.DictReader(file):
                day = date.fromisoformat(row.get("observation_date") or row["DATE"])
                if YEARS[0] <= day <= YEARS[1] and row[key] not in ("","."):
                    table[day] = float(row[key])
        payload = "\n".join(f"{day},{value:.8f}" for day,value in sorted(table.items()))
        hashes[key] = sha256(payload.encode()).hexdigest()
        outputs.append(table)
    return outputs,hashes


def shifted_month(day, months):
    year, month = divmod(day.year*12+day.month-1+months,12)
    return date(year,month+1,1)


def observations(tables):
    fx,usd,jpy = tables
    days = sorted(fx)
    dollars = sorted(usd)
    records = []
    for a,b in zip(days,days[1:]):
        if b < date(2004,1,1):
            continue
        us_i = bisect_right(dollars,a-timedelta(days=2))-1
        yen_month = shifted_month(a,-2)
        if us_i<0 or yen_month not in jpy:
            raise ValueError(f"Missing lagged rate for interval starting {a}")
        fraction = (b-a).days/365
        records.append((a,b,[log(fx[b]/fx[a]),usd[dollars[us_i]]/100*fraction,
                             jpy[yen_month]/100*fraction,fraction]))
    return records


def components(data, spread_bp):
    log_fx, usd, jpy, duration = np.moveaxis(np.asarray(data),-1,0)
    conversion = np.exp(-log_fx)
    fx = 1-conversion
    carry = usd-jpy
    interaction = jpy*fx
    fee = -conversion*spread_bp/10000*duration
    return np.stack((fx,carry,interaction,fee),axis=-1)


def accounts(pnl, leverage):
    initial = 1/leverage
    equity = np.c_[np.full(len(pnl),initial),
                   initial-OPEN_EXIT+np.cumsum(pnl,axis=1)]
    breach = equity[:,1:] <= .4*initial
    has_breached = np.any(breach,axis=1)
    stop = np.where(has_breached,np.argmax(breach,axis=1)+1,pnl.shape[1])
    index = np.arange(len(pnl))
    equity[index,stop] -= OPEN_EXIT
    equity = np.take_along_axis(equity,np.minimum(np.arange(equity.shape[1]),stop[:,None]),axis=1)
    close = equity[:,-1]/initial-1
    drawdown = np.max(np.maximum.accumulate(equity,axis=1)-equity,axis=1)/initial
    return close,drawdown,has_breached


def blocks(rng, source, count, horizon, block):
    offsets = rng.integers(0,len(source)-block+1,size=(count,(horizon+block-1)//block,1))
    index = (offsets+np.arange(block)).reshape(count,-1)[:,:horizon]
    return source[index]


def metrics(paths, name, block, spread, leverage):
    close,draw,breach = accounts(components(paths,spread).sum(axis=-1),leverage)
    p = float(np.mean(breach))
    return (dict(generator=name,block=block,spread_bp=spread,leverage=leverage,n=len(close),
                 drawdown_p95=np.quantile(draw,.95),closeout_p05=np.quantile(close,.05),
                 breach=p,simulation_se=np.sqrt(p*(1-p)/len(close)) if name!="Replay" else None),draw)


def analyze(records, quick):
    count,horizon = (300,5) if quick else (4000,21)
    train = np.array([value for _,b,value in records if b.year<=2021])
    out = np.array([value for _,b,value in records if b.year>=2022])
    if len(train) < 30 or len(out)<horizon:
        raise ValueError("Insufficient calibration or holdout data")
    replay = out[:len(out)//horizon*horizon].reshape(-1,horizon,4)
    schedules = blocks(np.random.default_rng([SEED,20]),train,count,horizon,5)
    gaussian = schedules.copy()
    gaussian[:,:,0] = np.random.default_rng([SEED,30]).normal(train[:,0].mean(),train[:,0].std(ddof=1),(count,horizon))
    trials = [("Gaussian",0,gaussian),("Replay",0,replay)]
    for length in (5,) if quick else (2,5,10):
        resample = schedules.copy()
        resample[:,:,0] = blocks(np.random.default_rng([SEED,length]),train[:,0],count,horizon,length)
        trials.append(("Blocks",length,resample))
    rows, samples = [], {}
    for name,length,values in trials:
        for spread in COSTS:
            for lev in LEV:
                row, draws = metrics(values,name,length,spread,lev)
                rows.append(row)
                if spread==50 and lev==15 and (name!="Blocks" or length==5):
                    samples[name] = draws
    return rows,samples,len(train),len(out)


def fixture():
    rng = np.random.default_rng(71)
    days = [date(2021,11,1)+timedelta(days=i) for i in range(150)]
    values = rng.normal(.0001,.009,len(days))
    return [(day-timedelta(days=1),day,[m,.05/365,.001/365,1/365]) for day,m in zip(days,values)]


def figures(out,rows,samples,replay,fixture_label):
    colors = ("#166c77","#a14064","#8c5838")
    yrs = "Synthetic fixture" if fixture_label else "Fed H.10 and lagged rate proxies · fixed USD notional"
    p = Plot("Liquidation sensitivity",yrs+" · 5-interval blocks",(3,25),(0,100),
             "Initial leverage (×)","Breach fraction (%)")
    for spread,color in zip(COSTS,colors):
        p.series([(r["leverage"],100*r["breach"]) for r in rows if r["generator"]=="Blocks"
                  and r["block"]==5 and r["spread_bp"]==spread],color,f"{spread} bp cost")
    p.save(out/"sensitivity.svg")
    p = Plot("Simulated and realized drawdowns",yrs+" · 15× leverage / 50 bp funding spread",
             (0,100),(0,max(float(np.max(a)) for a in samples.values())*105),
             "Drawdown percentile","Drawdown / initial margin (%)")
    for (name,draw),color in zip(samples.items(),colors):
        q = np.linspace(0,1,101)
        p.series(zip(q*100,np.quantile(draw,q)*100),color,name,dots=False)
    p.save(out/"drawdown.svg")

    if replay is not None:
        totals = replay.sum(axis=0)*100
        labels = ("Start","FX","Net interest","Conversion","Funding cost","Entry / exit")
        points = np.r_[0,np.cumsum(totals),totals.sum()-2*OPEN_EXIT*100]
        lower,upper = min(points)-.5,max(points)+.5
        p = Plot("August 1–7, 2024 P&L bridge","Unliquidated path · dollars per $100 notional",
                 (0,len(labels)-1),(lower,upper),"Cumulative P&L by component","P&L (USD)",
                 x_ticks=list(enumerate(labels)))
        p.series(list(enumerate(points)),"#166c77","P&L after each component")
        p.save(out/"waterfall.svg")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--quick",action="store_true")
    parser.add_argument("--download",action="store_true")
    parser.add_argument("--data",type=Path,default=ROOT/"data")
    parser.add_argument("--output",type=Path,default=ROOT/"private-report")
    args=parser.parse_args()
    if args.quick:
        records, hashes = fixture(), {}
    else:
        tables, hashes = read_data(args.data,args.download)
        expected = json.loads((ROOT/"source-hashes.json").read_text())
        if hashes != expected:
            raise ValueError(f"Observation slice revised: expected {expected}, received {hashes}")
        records=observations(tables)
    rows,samples,train,holdout=analyze(records,args.quick)
    args.output.mkdir(exist_ok=True,parents=True)
    replay = [(a,b,value) for a,b,value in records if a>=date(2024,8,1) and b<=date(2024,8,7)]
    pnl = components(np.array([v for _,_,v in replay]),50) if replay else None
    figures(args.output,rows,samples,pnl,args.quick)
    with (args.output/"scenarios.csv").open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{train} training and {holdout} holdout intervals")
    for row in rows:
        if row["leverage"]==15 and row["spread_bp"]==50 and row["block"] in (0,5):
            print(row)
    if replay:
        print("Aug. 1–7 components per $100 notional:",pnl.sum(axis=0)*100)
        print("Aug. 1–5 components per $100 notional:",pnl[:2].sum(axis=0)*100)
        for lev in LEV:
            close,draw,breach = accounts(pnl.sum(axis=1)[None,:],lev)
            print(f"August replay at {lev}x: closeout {close[0]:.3%}, drawdown {draw[0]:.3%}, breach {breach[0]}")


if __name__=="__main__":
    main()
