import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, EVENT, FONT, TEAM} from '../theme';

export default makeScene2D('01-title', function* (view) {
  const kicker = createRef<Rect>();
  const title = createRef<Txt>();
  const rule = createRef<Rect>();
  const sub = createRef<Txt>();
  const team = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={EVENT.toUpperCase()} x={-660} y={-330} />);
  view.add(
    <Txt
      ref={title}
      text={'Inteligentny asystent\nurzędnika'}
      x={-620}
      y={-110}
      offsetX={-1}
      offsetY={-0.5}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={112}
      fontWeight={800}
      lineHeight={124}
      letterSpacing={-3.4}
      opacity={0}
    />,
  );
  view.add(
    <Rect ref={rule} width={0} height={4} radius={2} fill={COLORS.blue} x={-618} y={72} offsetX={-1} />,
  );
  view.add(
    <Txt
      ref={sub}
      text={'Wniosek wchodzi. Pismo wychodzi. Decyzja zostaje po stronie urzędnika.'}
      x={-620}
      y={140}
      offsetX={-1}
      offsetY={-0.5}
      width={1300}
      textWrap
      textAlign={'left'}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={30}
      fontWeight={400}
      lineHeight={44}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={team}
      text={`ZESPÓŁ  ·  ${TEAM.join('  ·  ')}`}
      x={-620}
      y={272}
      offsetX={-1}
      offsetY={-0.5}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={22}
      fontWeight={500}
      letterSpacing={1.6}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.5, easeOutCubic), kicker().x(-620, 0.5, easeOutCubic));
  yield* all(title().opacity(1, 0.7, easeOutCubic), title().y(-150, 0.7, easeOutCubic));
  yield* all(
    rule().width(120, 0.5, easeOutCubic),
    sub().opacity(1, 0.6, easeOutCubic),
    team().opacity(1, 0.6, easeOutCubic),
  );
  yield* waitFor(6.2);
});
