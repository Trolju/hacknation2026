import {makeScene2D, Rect, Video} from '@revideo/2d';
import {all, createRef, easeInOutCubic, easeOutBack, easeOutCubic, waitFor} from '@revideo/core';
import {
  Backdrop,
  CardScrim,
  CardVignette,
  FootageCard,
  ModuleCaption,
  ProgressRail,
  ResultChip,
  Sweep,
  camPos,
} from '../components';
import {FEATURES, featureDuration, type CamKey, type Feature} from '../features';

/** Płynny przejazd kamery po nagraniu, w czasie sceny. */
function* cameraMove(video: () => Video, keys: CamKey[], rate: number, dur: number) {
  // Ostatni klucz nie może wypaść dokładnie na końcu nagrania — seek poza zakres.
  const scene = keys.map(k => ({...k, t: Math.min(k.t, dur - 0.08) / rate}));
  for (let i = 1; i < scene.length; i++) {
    const a = scene[i - 1];
    const b = scene[i];
    const dt = Math.max(0.1, b.t - a.t);
    const p = camPos(b.fx, b.fy, b.z);
    yield* all(
      video().scale(b.z, dt, easeInOutCubic),
      video().position.x(p.x, dt, easeInOutCubic),
      video().position.y(p.y, dt, easeInOutCubic),
    );
  }
}

export function makeFeatureScene(f: Feature, active: number) {
  return makeScene2D(`feat-${f.id}`, function* (view) {
    const card = createRef<Rect>();
    const video = createRef<Video>();
    const caption = createRef<Rect>();
    const chip = createRef<Rect>();
    const sweep = createRef<Rect>();

    view.add(<Backdrop grid={false} />);
    view.add(<FootageCard src={f.clip} rate={f.rate} cardRef={card} videoRef={video} />);
    view.add(<CardScrim />);
    view.add(<CardVignette />);
    view.add(<ModuleCaption index={f.index} name={f.name} benefit={f.benefit} accent={f.accent} ref={caption} />);
    view.add(<ResultChip text={f.result} accent={f.accent} ref={chip} />);
    view.add(<ProgressRail total={FEATURES.length} active={active} accent={f.accent} />);
    view.add(<Sweep ref={sweep} color={f.accent} />);

    const c0 = f.camera[0];
    const p0 = camPos(c0.fx, c0.fy, c0.z);
    video().scale(c0.z);
    video().position.x(p0.x);
    video().position.y(p0.y);

    card().scale(1.06);
    caption().y(30);

    const clipScene = f.dur / f.rate;

    yield* all(
      card().opacity(1, 0.26, easeOutCubic),
      card().scale(1, 0.42, easeOutCubic),
      sweep().x(1100, 0.6, easeInOutCubic),
      caption().opacity(1, 0.42, easeOutCubic),
      caption().y(0, 0.5, easeOutCubic),
      cameraMove(video, f.camera, f.rate, f.dur),
    );

    // Nagranie skończone — zatrzymujemy odtwarzanie, żeby nie szukać poza końcem.
    video().pause();

    yield* all(chip().opacity(1, 0.26, easeOutCubic), chip().scale(1, 0.34, easeOutBack));
    yield* waitFor(Math.max(0.1, f.hold - 0.3));
  });
}

export const featureDurations = FEATURES.map(featureDuration);
