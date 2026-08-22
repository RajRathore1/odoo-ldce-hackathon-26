"use client";

import { useId, useMemo, useState } from "react";

type Point = { label: string; users: number };

const WIDTH = 600;
const HEIGHT = 220;
const PAD_X = 12;
const PAD_Y = 16;

export function TrendChart({ data }: { data: Point[] }) {
  const gradientId = useId();
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const max = Math.max(...data.map((point) => point.users), 1);

  const points = useMemo(() => {
    const innerWidth = WIDTH - PAD_X * 2;
    const innerHeight = HEIGHT - PAD_Y * 2;
    return data.map((point, index) => {
      const x =
        PAD_X +
        (data.length === 1
          ? innerWidth / 2
          : (index / (data.length - 1)) * innerWidth);
      const y = PAD_Y + innerHeight - (point.users / max) * innerHeight;
      return { x, y, ...point };
    });
  }, [data, max]);

  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");

  const areaPath = `${linePath} L ${points[points.length - 1].x} ${HEIGHT - PAD_Y} L ${points[0].x} ${HEIGHT - PAD_Y} Z`;

  function handleMove(event: React.MouseEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = ((event.clientX - rect.left) / rect.width) * WIDTH;
    let closest = 0;
    let closestDistance = Infinity;
    points.forEach((point, index) => {
      const distance = Math.abs(point.x - relativeX);
      if (distance < closestDistance) {
        closestDistance = distance;
        closest = index;
      }
    });
    setHoverIndex(closest);
  }

  const active = hoverIndex !== null ? points[hoverIndex] : null;

  return (
    <div>
      <div className="relative">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full cursor-crosshair"
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="var(--color-primary)"
                stopOpacity="0.22"
              />
              <stop
                offset="100%"
                stopColor="var(--color-primary)"
                stopOpacity="0"
              />
            </linearGradient>
          </defs>

          <path d={areaPath} fill={`url(#${gradientId})`} />
          <path
            d={linePath}
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {active && (
            <line
              x1={active.x}
              x2={active.x}
              y1={PAD_Y}
              y2={HEIGHT - PAD_Y}
              stroke="var(--color-border)"
              strokeDasharray="4 3"
            />
          )}

          {points.map((point, index) => (
            <circle
              key={point.label}
              cx={point.x}
              cy={point.y}
              r={hoverIndex === index ? 5 : 3}
              fill={
                hoverIndex === index
                  ? "var(--color-accent)"
                  : "var(--color-primary)"
              }
            />
          ))}
        </svg>

        {active && (
          <div
            className="pointer-events-none absolute -translate-x-1/2 -translate-y-full rounded-lg bg-primary px-2.5 py-1.5 text-xs font-medium whitespace-nowrap text-white shadow-lg"
            style={{
              left: `${(active.x / WIDTH) * 100}%`,
              top: `${(active.y / HEIGHT) * 100}%`,
            }}
          >
            {active.users.toLocaleString("en-IN")}
            <span className="ml-1 text-white/60">{active.label}</span>
          </div>
        )}
      </div>

      <div className="mt-2 flex justify-between text-xs text-text-muted">
        {data.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
    </div>
  );
}
