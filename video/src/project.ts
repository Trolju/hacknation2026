import {makeProject} from '@revideo/core';

import './assets/fonts/inter-local.css';

import title from './scenes/01-title';
import problem from './scenes/02-problem';
import flow from './scenes/03-flow';
import demo from './scenes/04-demo';
import tech from './scenes/05-tech';
import future from './scenes/06-future';
import offline from './scenes/07-offline';
import outro from './scenes/08-outro';

export default makeProject({
  name: 'asystent-urzednika',
  scenes: [title, problem, flow, demo, tech, future, offline, outro],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
