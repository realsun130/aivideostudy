import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Minimal 3s demo: a circle bounces and a label fades in.
 * Intentionally tiny — not wired to Cavalier rig.
 */
export const Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const bounce = Math.abs(Math.sin((frame / fps) * Math.PI * 2));
  const y = interpolate(bounce, [0, 1], [40, -80]);
  const opacity = interpolate(frame, [0, 15, durationInFrames - 15, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: "50%",
          backgroundColor: "#e94560",
          transform: `translateY(${y}px)`,
          boxShadow: "0 8px 24px rgba(233, 69, 96, 0.45)",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 48,
          opacity,
          color: "#eee",
          fontSize: 28,
          letterSpacing: 1,
        }}
      >
        Remotion local render
      </div>
    </AbsoluteFill>
  );
};
