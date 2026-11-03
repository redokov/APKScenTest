import React from 'react';

export const W = 1600;
export const H = 900;

export const C = {
  bg: '#f4f6fb',
  ink: '#1e293b',
  muted: '#475569',
  card: '#ffffff',
  border: '#cbd5e1',
  blue: '#2563eb',
  green: '#16a34a',
  purple: '#7c3aed',
  amber: '#d97706',
  red: '#dc2626',
  teal: '#0d9488',
  softBlue: '#dbeafe',
  softGreen: '#dcfce7',
  softAmber: '#fef3c7',
  softRed: '#fee2e2',
  softPurple: '#ede9fe',
};

export const FONT = "'Segoe UI', 'Segoe UI Symbol', Arial, sans-serif";

export const Page: React.FC<{title: string; subtitle?: string; children: React.ReactNode}> = ({
  title,
  subtitle,
  children,
}) => (
  <div
    style={{
      width: W,
      height: H,
      background: C.bg,
      fontFamily: FONT,
      color: C.ink,
      display: 'flex',
      flexDirection: 'column',
      padding: '48px 56px 40px',
      boxSizing: 'border-box',
    }}
  >
    <div style={{fontSize: 46, fontWeight: 700, lineHeight: 1.15}}>{title}</div>
    {subtitle ? (
      <div style={{fontSize: 24, color: C.muted, marginTop: 10, lineHeight: 1.35}}>{subtitle}</div>
    ) : null}
    <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      {children}
    </div>
  </div>
);

export const Card: React.FC<{
  title: string;
  chip?: string;
  chipColor?: string;
  bullets?: string[];
  note?: string;
  width?: number;
  height?: number;
  accent?: string;
}> = ({title, chip, chipColor = C.blue, bullets = [], note, width, height, accent = C.blue}) => (
  <div
    style={{
      width,
      height,
      background: C.card,
      border: `2px solid ${C.border}`,
      borderTop: `8px solid ${accent}`,
      borderRadius: 18,
      boxShadow: '0 10px 28px rgba(15,23,42,0.10)',
      padding: '22px 26px',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14}}>
      {chip ? (
        <div
          style={{
            background: chipColor,
            color: '#fff',
            borderRadius: 999,
            padding: '6px 18px',
            fontSize: 21,
            fontWeight: 700,
            whiteSpace: 'nowrap',
          }}
        >
          {chip}
        </div>
      ) : null}
      <div style={{fontSize: 27, fontWeight: 700, lineHeight: 1.2}}>{title}</div>
    </div>
    {bullets.map((b, i) => (
      <div key={i} style={{display: 'flex', gap: 10, marginBottom: 10, alignItems: 'flex-start'}}>
        <div style={{color: accent, fontSize: 22, fontWeight: 700, lineHeight: 1.3}}>•</div>
        <div style={{fontSize: 21, lineHeight: 1.35, color: C.ink}}>{b}</div>
      </div>
    ))}
    {note ? (
      <div
        style={{
          marginTop: 'auto',
          background: '#f1f5f9',
          borderRadius: 10,
          padding: '10px 14px',
          fontSize: 18.5,
          color: C.muted,
          lineHeight: 1.35,
        }}
      >
        {note}
      </div>
    ) : null}
  </div>
);

export const Arrow: React.FC<{color?: string; width?: number; height?: number; label?: string}> = ({
  color = C.muted,
  width = 64,
  height = 26,
  label,
}) => (
  <div
    style={{
      width,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
    }}
  >
    {label ? (
      <div style={{fontSize: 15, color: C.muted, marginBottom: 3, whiteSpace: 'normal', textAlign: 'center'}}>{label}</div>
    ) : null}
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <line
        x1={2}
        y1={height / 2}
        x2={width - height * 0.7 - 2}
        y2={height / 2}
        stroke={color}
        strokeWidth={5}
      />
      <polygon
        points={`${width - 2},${height / 2} ${width - height * 0.8},${height / 2 - height / 3} ${
          width - height * 0.8
        },${height / 2 + height / 3}`}
        fill={color}
      />
    </svg>
  </div>
);

export const Ribbon: React.FC<{items: {text: string; color: string}[]}> = ({items}) => (
  <div style={{display: 'flex', gap: 24, marginTop: 34, justifyContent: 'center'}}>
    {items.map((it, i) => (
      <div
        key={i}
        style={{
          background: it.color,
          color: '#fff',
          borderRadius: 999,
          padding: '14px 30px',
          fontSize: 23,
          fontWeight: 600,
          boxShadow: '0 8px 20px rgba(15,23,42,0.14)',
        }}
      >
        {it.text}
      </div>
    ))}
  </div>
);

export const Pill: React.FC<{text: string; color: string; big?: boolean}> = ({text, color, big}) => (
  <div
    style={{
      background: color,
      color: '#fff',
      borderRadius: 16,
      padding: big ? '18px 34px' : '10px 22px',
      fontSize: big ? 32 : 21,
      fontWeight: 700,
      boxShadow: '0 8px 20px rgba(15,23,42,0.16)',
      whiteSpace: 'nowrap',
    }}
  >
    {text}
  </div>
);
