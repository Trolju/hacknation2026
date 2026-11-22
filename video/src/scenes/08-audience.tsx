import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, delay, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const LEFT = -840;

const PANELS = [
  {
    label: 'DLA KOGO',
    color: COLORS.sky,
    title: 'Urzędnicy obsługujący wnioski UDIP',
    items: [
      'Referenci i podinspektorzy w komórkach merytorycznych.',
      'Osoby, które przygotowują odpowiedzi na wnioski o informację publiczną.',
      'Zespoły szukające wiedzy w archiwum, a nie w czyjejś głowie.',
    ],
  },
  {
    label: 'W BYDGOSZCZY',
    color: COLORS.green,
    title: 'Od prototypu do stałego wdrożenia',
    items: [
      'Skalowanie do setek dokumentów i wieloletniego archiwum.',
      'Model lokalny w serwerowni urzędu — bez ruchu na zewnątrz.',
      'Kolejne kroki: BIP, rejestr pism, e-doręczenia.',
    ],
  },
];

const PANEL_W = 820;
const PANEL_H = 560;

export default makeScene2D('08-audience', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const panels = PANELS.map(() => createRef<Rect>());

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'DLA KOGO I CO DALEJ'} x={LEFT - 40} y={-400} color={COLORS.sky} />);
  view.add(
    <Txt
      ref={head}
      text={'Asystent, nie zamiennik decyzji.'}
      x={LEFT}
      y={-330}
      offsetX={-1}
      offsetY={-0.5}
      width={1500}
      textWrap
      textAlign={'left'}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={66}
      fontWeight={700}
      lineHeight={78}
      letterSpacing={-1.4}
      opacity={0}
    />,
  );

  view.add(
    <Rect layout={false}>
      {PANELS.map((p, i) => (
        <Rect
          ref={panels[i]}
          key={p.label}
          x={i === 0 ? -PANEL_W / 2 - 20 : PANEL_W / 2 + 20}
          y={100}
          width={PANEL_W}
          height={PANEL_H}
          radius={22}
          fill={'#0A1220'}
          stroke={'#1E2A3D'}
          lineWidth={1.5}
          layout={false}
          opacity={0}
        >
          <Rect width={PANEL_W - 80} height={4} radius={2} fill={p.color} y={-PANEL_H / 2 + 26} />
          <Txt
            text={p.label}
            x={-PANEL_W / 2 + 40}
            y={-PANEL_H / 2 + 66}
            offsetX={-1}
            offsetY={-0.5}
            fill={p.color}
            fontFamily={FONT}
            fontSize={17}
            fontWeight={700}
            letterSpacing={3}
          />
          <Txt
            text={p.title}
            x={-PANEL_W / 2 + 40}
            y={-PANEL_H / 2 + 118}
            offsetX={-1}
            offsetY={-0.5}
            width={PANEL_W - 80}
            textWrap
            textAlign={'left'}
            fill={COLORS.text}
            fontFamily={FONT}
            fontSize={34}
            fontWeight={700}
            lineHeight={42}
            letterSpacing={-0.6}
          />
          {p.items.map((it, j) => (
            <Rect key={it} x={-PANEL_W / 2 + 40} y={-PANEL_H / 2 + 210 + j * 96} layout={false}>
              <Rect width={3} height={26} radius={2} fill={p.color} x={0} y={-14} />
              <Txt
                text={it}
                x={22}
                y={-14}
                offsetX={-1}
                offsetY={-0.5}
                width={PANEL_W - 130}
                textWrap
                textAlign={'left'}
                fill={COLORS.muted}
                fontFamily={FONT}
                fontSize={22}
                fontWeight={400}
                lineHeight={31}
              />
            </Rect>
          ))}
        </Rect>
      ))}
    </Rect>,
  );

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(head().opacity(1, 0.5, easeOutCubic), head().y(-322, 0.5, easeOutCubic));

  yield* all(
    ...PANELS.map((_, i) =>
      delay(
        i * 0.2,
        all(panels[i]().opacity(1, 0.5, easeOutCubic), panels[i]().y(86, 0.55, easeOutExpo)),
      ),
    ),
  );

  yield* waitFor(4.2);
});
