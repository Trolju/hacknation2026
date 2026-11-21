import {makeScene2D, Img, Rect} from '@revideo/2d';
import {all, createRef, easeInOutCubic, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, BrowserCard, Headline, Kicker, ProgressDots, Subline} from '../components';
import {COLORS} from '../theme';

import pulpit from '../assets/shots/pulpit.png';
import kalendarz from '../assets/shots/kalendarz.png';
import kalendarzDetail from '../assets/shots/kalendarz_detail.png';
import dokumenty from '../assets/shots/dokumenty_uploaded.png';
import archiwum from '../assets/shots/archiwum_results.png';
import wydzialy from '../assets/shots/wydzialy_query.png';
import odpowiedzi from '../assets/shots/odpowiedzi_draft.png';
import anonimizacja from '../assets/shots/anonimizacja_result.png';
import ustawienia from '../assets/shots/ustawienia.png';

const SLIDES = [
  {
    img: pulpit,
    url: '127.0.0.1:5173/',
    head: 'Dzień zaczyna się od jednego ekranu',
    sub: 'Po terminie, na dziś, na jutro — bez szukania w arkuszu.',
  },
  {
    img: kalendarz,
    url: '127.0.0.1:5173/kalendarz',
    head: 'Wszystkie wnioski według terminu',
    sub: 'Dni i pilność liczy serwer przy każdym odczycie — nie da się ich rozjechać.',
  },
  {
    img: kalendarzDetail,
    url: '127.0.0.1:5173/kalendarz',
    head: 'Stan sprawy i pełna historia',
    sub: 'Cofnięcie stanu wymaga notatki — w sprawie zostaje ślad.',
  },
  {
    img: dokumenty,
    url: '127.0.0.1:5173/dokumenty',
    head: 'Wgranie wniosku w PDF lub DOCX',
    sub: 'Tekst rozpoznany, podzielony na fragmenty i zapisany w bazie wiedzy.',
  },
  {
    img: archiwum,
    url: '127.0.0.1:5173/archiwum',
    head: 'Podobne sprawy z przeszłości',
    sub: 'Wniosek o wynagrodzenia: trafienie 0,71 w sprawie z 2025 roku.',
  },
  {
    img: wydzialy,
    url: '127.0.0.1:5173/wydzialy',
    head: 'Które komórki mają odpowiedzieć',
    sub: 'Pięć komórek, pewność 95% dla Wydziału Organizacji i Kadr.',
  },
  {
    img: odpowiedzi,
    url: '127.0.0.1:5173/odpowiedzi',
    head: 'Projekt pisma z cytowaniami',
    sub: 'Każde twierdzenie ma źródło; braki widać przed wysłaniem.',
  },
  {
    img: anonimizacja,
    url: '127.0.0.1:5173/anonimizacja',
    head: 'Dane osobowe wykryte i usunięte',
    sub: 'PESEL, adres, telefon, e-mail — precyzja 100% na zbiorze testowym.',
  },
  {
    img: ustawienia,
    url: '127.0.0.1:5173/ustawienia',
    head: 'Tryb każdego modułu pod kontrolą',
    sub: 'Osiem modułów: atrapa albo implementacja realna.',
  },
];

const SLIDE_SECONDS = 10;

export default makeScene2D('04-demo', function* (view) {
  const groups = SLIDES.map(() => createRef<Rect>());
  const images = SLIDES.map(() => createRef<Img>());

  view.add(<Backdrop />);

  SLIDES.forEach((s, i) => {
    view.add(
      <Rect ref={groups[i]} layout={false} opacity={0}>
        <Kicker text={`PROTOTYP  ·  ${i + 1} / ${SLIDES.length}`} x={-620} y={-478} />
        <Headline text={s.head} x={-620} y={-424} size={46} width={1500} />
        <Subline text={s.sub} x={-620} y={-374} size={24} width={1500} />
        <BrowserCard src={s.img} url={s.url} width={1120} y={90} imageRef={images[i]} />
        <ProgressDots total={SLIDES.length} active={i} y={500} />
      </Rect>,
    );
  });

  for (let i = 0; i < SLIDES.length; i++) {
    yield images[i]().scale(1.03, SLIDE_SECONDS - 0.5, easeInOutCubic);
    yield* groups[i]().opacity(1, 0.45, easeOutCubic);
    yield* waitFor(SLIDE_SECONDS - 0.9);
    yield* groups[i]().opacity(0, 0.45, easeOutCubic);
  }
});
