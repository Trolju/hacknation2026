import {makeProject} from '@revideo/core';

import './assets/fonts/inter-local.css';

import {FEATURES} from './features';
import intro from './scenes/01-intro';
import problem from './scenes/02-problem';
import modules from './scenes/03-modules';
import {makeFeatureScene} from './scenes/04-feature';
import workflow from './scenes/05-workflow';
import stack from './scenes/06-stack';
import offline from './scenes/07-offline';
import audience from './scenes/08-audience';
import outro from './scenes/09-outro';

const features = FEATURES.map((f, i) => makeFeatureScene(f, i));

export default makeProject({
  name: 'asystent-urzednika',
  scenes: [intro, problem, modules, ...features, workflow, stack, offline, audience, outro],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
