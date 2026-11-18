from html import escape


class Plot:
    def __init__(self, title, subtitle, xlim, ylim, xlabel, ylabel, x_ticks=None):
        self.xlim, self.ylim = xlim, ylim
        self.count = 0
        self.parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="455" viewBox="0 0 760 455" role="img">',
                      f"<title>{escape(title)}. {escape(subtitle)}</title>",
                      '<rect width="760" height="455" fill="#fbfaf6"/>',
                      '<g fill="#152637" font-family="Arial,sans-serif">']
        self.text(25, 34, title, size=23)
        self.text(25, 57, subtitle, size=13)
        for tick in range(6):
            y = ylim[0] + tick * (ylim[1]-ylim[0]) / 5
            _, pixel = self.point(xlim[0], y)
            self.parts.append(f'<path d="M90 {pixel}H735" stroke="#d9ddda"/>')
            self.text(82, pixel+4, f"{y:.3g}", anchor="end")
        if x_ticks is None:
            x_ticks = [(xlim[0]+i*(xlim[1]-xlim[0])/5, None) for i in range(6)]
        for x, label in x_ticks:
            pixel, _ = self.point(x, ylim[0])
            self.text(pixel, 375, label if label is not None else f"{x:.3g}", anchor="middle")
        self.text(412, 399, xlabel, anchor="middle", size=14)
        self.parts.append(f'<text x="20" y="223" transform="rotate(-90 20 223)" text-anchor="middle" font-size="14">{escape(ylabel)}</text>')

    def point(self, x, y):
        return (90+645*(x-self.xlim[0])/(self.xlim[1]-self.xlim[0]),
                355-265*(y-self.ylim[0])/(self.ylim[1]-self.ylim[0]))

    def text(self, x, y, value, anchor="start", size=12):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}">{escape(value)}</text>')

    def series(self, points, color, label, *, dots=True, line=True):
        coords = [self.point(x, y) for x, y in points]
        if line:
            path = " ".join(f"{x:.2f},{y:.2f}" for x, y in coords)
            self.parts.append(f'<polyline points="{path}" stroke="{color}" stroke-width="2" fill="none"/>')
        if dots:
            for x, y in coords:
                self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
        left = 95 + self.count * 200
        self.parts.append(f'<path d="M{left} 429h18" stroke="{color}" stroke-width="3"/>')
        self.text(left+24, 433, label)
        self.count += 1

    def save(self, path):
        path.write_text("\n".join(self.parts + ["</g></svg>"])+"\n", encoding="utf-8")
