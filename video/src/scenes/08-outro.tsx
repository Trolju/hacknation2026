import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop} from '../components';
import {COLORS, EVENT, FONT, TEAM} from '../theme';

export default makeScene2D('08-outro', function* (view) {
  const name = createRef<Txt>();
  const rule = createRef<Rect>();
  const tagline = createRef<Txt>();
  const meta = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(
    <Txt
      ref={name}
      text={'Inteligentny asystent urzędnika'}
      y={-190}
      offsetY={-0.5}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={78}
      fontWeight={800}
      letterSpacing={-2.4}
      opacity={0}
    />,
  );
  view.add(<Rect ref={rule} width={0} height={4} radius={2} fill={COLORS.blue} y={-80} />);
  view.add(
    <Txt
      ref={tagline}
      text={'Odpowiedź w minutach, nie w dniach.'}
      y={20}
      offsetY={-0.5}
      fill={COLORS.sky}
      fontFamily={FONT}
      fontSize={44}
      fontWeight={600}
      letterSpacing={-0.6}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={meta}
      text={`${EVENT.toUpperCase()}\nZESPÓŁ  ·  ${TEAM.join('  ·  ')}`}
      y={190}
      offsetY={-0.5}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={21}
      fontWeight={500}
      lineHeight={40}
      letterSpacing={1.6}
      opacity={0}
    />,
  );

  yield* all(name().opacity(1, 0.6, easeOutCubic), name().y(-210, 0.6, easeOutCubic));
  yield* rule().width(160, 0.5, easeOutCubic);
  yield* all(tagline().opacity(1, 0.6, easeOutCubic), meta().opacity(1, 0.6, easeOutCubic));
  yield* waitFor(6.0);
});
