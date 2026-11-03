import React from 'react';
import {Composition} from 'remotion';
import {TesterBatches, TesterPasswords, TesterPipeline, TesterRegression} from './diagrams';

const still = (id: string, comp: React.FC) => (
  <Composition
    id={id}
    component={comp}
    durationInFrames={1}
    fps={1}
    width={1600}
    height={900}
  />
);

export const Root: React.FC = () => (
  <>
    {still('TesterPipeline', TesterPipeline)}
    {still('TesterPasswords', TesterPasswords)}
    {still('TesterBatches', TesterBatches)}
    {still('TesterRegression', TesterRegression)}
  </>
);
