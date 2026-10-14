import React from "react";
import { Composition } from "remotion";
import { Demo } from "./Demo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Demo"
        component={Demo}
        durationInFrames={90}
        fps={30}
        width={640}
        height={360}
      />
    </>
  );
};
