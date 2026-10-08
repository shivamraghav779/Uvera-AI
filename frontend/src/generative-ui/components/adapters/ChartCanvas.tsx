/**
 * Chart drawing shared by adapters (Recharts). Loaded lazily.
 *
 * Colours are CSS variables from the theme, so a chart follows theme changes
 * without re-rendering its data.
 */
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART_COLOR_VARIABLES, TONE_VARIABLE } from "../../theme/themeTokens";

import type { ChartViewProps } from "./types";

const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });
const full = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });

const AXIS = { stroke: "var(--g-muted-fg)", fontSize: 12, tickLine: false, axisLine: false } as const;
const TOOLTIP_STYLE = {
  background: "var(--g-surface)",
  border: "1px solid var(--g-border)",
  borderRadius: "var(--g-radius)",
  color: "var(--g-fg)",
  fontSize: 12,
};

function formatTick(value: unknown): string {
  return typeof value === "number" ? compact.format(value) : String(value);
}

function formatTooltip(value: unknown): string {
  return typeof value === "number" ? full.format(value) : String(value);
}

function humanise(key: string): string {
  return key.replace(/_/g, " ").replace(/^./, (first) => first.toUpperCase());
}

/** Legend text in the theme's text colour; the swatch already carries the series colour. */
function legendLabel(text: string) {
  return <span style={{ color: "var(--g-fg)" }}>{text}</span>;
}

export default function ChartCanvas({ chartType, rows, xKey, yKeys, tone }: ChartViewProps) {
  // A style tone recolours the first series; the rest keep the theme's palette.
  const palette = tone ? [TONE_VARIABLE[tone], ...CHART_COLOR_VARIABLES.slice(1)] : CHART_COLOR_VARIABLES;
  const color = (index: number) => palette[index % palette.length]!;
  const showLegend = yKeys.length > 1;
  const grid = <CartesianGrid stroke="var(--g-border)" strokeDasharray="3 3" vertical={false} />;
  const tooltip = (
    <Tooltip
      formatter={(value, name) => [formatTooltip(value), humanise(String(name))]}
      contentStyle={TOOLTIP_STYLE}
      cursor={{ fill: "var(--g-muted)", opacity: 0.5 }}
    />
  );
  const legend = showLegend ? <Legend formatter={(value) => legendLabel(humanise(String(value)))} /> : null;
  const margin = { top: 8, right: 12, bottom: 0, left: 0 };

  if (chartType === "pie" || chartType === "donut") {
    const valueKey = yKeys[0]!;
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={rows}
            dataKey={valueKey}
            nameKey={xKey}
            innerRadius={chartType === "donut" ? "58%" : 0}
            outerRadius="82%"
            paddingAngle={chartType === "donut" ? 2 : 0}
            stroke="var(--g-surface)"
            isAnimationActive={false}
          >
            {rows.map((_, index) => (
              <Cell key={index} fill={color(index)} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => formatTooltip(value)} contentStyle={TOOLTIP_STYLE} />
          <Legend formatter={(value) => legendLabel(String(value))} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "scatter") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={margin}>
          {grid}
          <XAxis dataKey={xKey} name={humanise(xKey)} tickFormatter={formatTick} {...AXIS} />
          <YAxis dataKey={yKeys[0]} name={humanise(yKeys[0]!)} tickFormatter={formatTick} width={48} {...AXIS} />
          {tooltip}
          <Scatter data={rows} fill={color(0)} isAnimationActive={false} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  const axes = (
    <>
      {grid}
      <XAxis dataKey={xKey} tickFormatter={formatTick} {...AXIS} />
      <YAxis tickFormatter={formatTick} width={48} {...AXIS} />
      {tooltip}
      {legend}
    </>
  );

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={margin}>
          {axes}
          {yKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color(index)}
              strokeWidth={2}
              dot={{ r: 3 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "area") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={margin}>
          {axes}
          {yKeys.map((key, index) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color(index)}
              fill={color(index)}
              fillOpacity={0.18}
              strokeWidth={2}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={margin}>
        {axes}
        {yKeys.map((key, index) => (
          <Bar key={key} dataKey={key} fill={color(index)} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
