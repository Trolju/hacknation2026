import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop} from '../components';
import {COLORS, EVENT, FONT, TEAM} from '../theme';

export default makeScene2D('09-outro', function* (view) {
  const rule = createRef<Rect>();
  const l1 = createRef<Txt>();
  const l2 = createRef<Txt>();
  const thanks = createRef<Txt>();
  const team = createRef<Txt>();
  const event = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Rect ref={rule} width={0} height={4} radius={2} fill={COLORS.blue} x={0} y={-190} />);
  view.add(
    <Txt
      ref={l1}
      text={'Inteligentny'}
      x={0}
      y={-110}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={112}
      fontWeight={800}
      letterSpacing={-4}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={l2}
      text={'asystent urzędnika'}
      x={0}
      y={10}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={112}
      fontWeight={800}
      letterSpacing={-4}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={thanks}
      text={'Dziękujemy. Pytania?'}
      x={0}
      y={150}
      fill={COLORS.sky}
      fontFamily={FONT}
      fontSize={38}
      fontWeight={600}
      letterSpacing={-0.6}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={team}
      text={TEAM.join('   ·   ')}
      x={0}
      y={240}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={24}
      fontWeight={500}
      letterSpacing={1.2}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={event}
      text={EVENT.toUpperCase()}
      x={0}
      y={312}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={18}
      fontWeight={600}
      letterSpacing={3.2}
      opacity={0}
    />,
  );

  yield* rule().width(220, 0.5, easeOutCubic);
  yield* all(l1().opacity(1, 0.45, easeOutCubic), l1().y(-118, 0.5, easeOutExpo));
  yield* all(l2().opacity(1, 0.45, easeOutCubic), l2().y(2, 0.5, easeOutExpo));
  yield* all(
    thanks().opacity(1, 0.45, easeOutCubic),
    team().opacity(1, 0.45, easeOutCubic),
    event().opacity(1, 0.45, easeOutCubic),
  );
  yield* waitFor(4.6);
});
