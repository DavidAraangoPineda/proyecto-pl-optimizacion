/*
 * El viaje del Simplex — presentación narrada por capítulos.
 * Los datos (window.DATOS_PL) los genera el motor propio en Python (lp/presentation.py):
 * tableros, razones, vértices, recorrido y sensibilidad. Aquí solo se animan y se narran.
 */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const D = window.DATOS_PL;
  const lienzo = new Dibujo.Lienzo($('lienzo'));
  const v2 = lienzo.v2;
  const v3 = lienzo.v3;
  const CANCELADO = { cancelado: true };

  let esc = D.principal;           // escena (problema) que se presenta
  let historiaId = 0;
  let capituloActual = -1;
  let ritmo = 1;

  // ====================================================================== utilidades

  function esperar(ms, id) {
    return new Promise((ok, mal) => setTimeout(() => (id === historiaId ? ok() : mal(CANCELADO)), ms / ritmo));
  }

  const suave = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  function animar(ms, fn, id) {
    return new Promise((ok, mal) => {
      const t0 = performance.now();
      const dur = ms / ritmo;
      const paso = () => {
        if (id !== historiaId) return mal(CANCELADO);
        const k = Math.min(1, (performance.now() - t0) / dur);
        fn(suave(k), k);
        if (k < 1) Dibujo.cuadro(paso);
        else ok();
      };
      Dibujo.cuadro(paso);
    });
  }

  /** Escapa un dato para insertarlo como texto dentro de HTML (innerHTML). */
  const E = (v) => String(v === null || v === undefined ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  /** Escapa cada elemento de una lista y los une. */
  const EL = (lista, sep = ', ') => lista.map(E).join(sep);

  /**
   * Tipografía matemática sobre HTML ya escapado: x1 → x₁ en cursiva, cj → c_j, "-" → "−" y 2/5 apilada.
   * Solo transforma el texto; las etiquetas HTML se dejan intactas.
   */
  function mate(html) {
    return String(html).split(/(<[^>]*>)/).map((parte, i) => (i % 2 ? parte : mateTexto(parte))).join('');
  }

  function mateTexto(t) {
    return t
      .replace(/(^|[\s(=,;:[·+−])-(?=[\dMa-zA-Z(])/g, '$1−')
      .replace(/ - /g, ' − ')
      .replace(/\b(\d+)\/(\d+)\b/g, '<span class="fr"><span>$1</span><span>$2</span></span>')
      .replace(/(?<![A-Za-z_])([xyseaz])(\d+)\b/g, '<i>$1</i><sub>$2</sub>')
      .replace(/\b([cz])j\b/g, '<i>$1</i><sub>j</sub>')
      .replace(/\b([cx])B\b/g, '<i>$1</i><sub>B</sub>')
      .replace(/\ba_e\b/g, '<i>a</i><sub>e</sub>')
      .replace(/\baj\b/g, '<i>a</i><sub>j</sub>')
      .replace(/\bZ(′?)(?=\s|$|\))/g, '<i>Z</i>$1')
      .replace(/(?<![A-Za-z])M(?![A-Za-z])/g, '<i>M</i>');
  }

  function textoPlano(html) {
    const d = document.createElement('div');
    d.innerHTML = html;
    return d.textContent;
  }

  /** Convierte el texto a algo que la voz lea bien en español. */
  function paraVoz(html) {
    let t = textoPlano(html);
    const sub = { '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9' };
    t = t.replace(/[₀-₉]/g, (c) => sub[c]);
    t = t.replace(/cj\s*[−-]\s*zj/g, 'c j menos z j');
    t = t.replace(/B⁻¹/g, 'B inversa');
    t = t.replace(/Z′|Z'/g, 'Z prima');
    t = t.replace(/(?<![A-Za-z_])([xsea])(\d+)\b/g, (m, l, d) => ({ x: ' equis ', s: ' ese ', e: ' e ', a: ' a ' }[l] + d));
    t = t.replace(/\((\d+)\/(\d+)\)M/g, '$1 sobre $2 eme');
    t = t.replace(/(-?\d+)\/(\d+)/g, '$1 sobre $2');
    t = t.replace(/(^|[\s(=,;:])[-−]\s?(?=[\dMa-zA-Z(])/g, '$1menos ');
    t = t.replace(/(\d)\s?M\b/g, '$1 eme');
    t = t.replace(/\bM\b/g, 'eme');
    t = t.replace(/≤/g, ' menor o igual que ').replace(/≥/g, ' mayor o igual que ');
    t = t.replace(/θ/g, 'theta').replace(/∞/g, 'infinito').replace(/→/g, ', ').replace(/·/g, ' ');
    t = t.replace(/\s=\s/g, ' igual a ');
    return t.replace(/\s+/g, ' ').trim();
  }

  function subtitulo(html) {
    const s = $('subtitulo');
    if (!html) {
      s.classList.remove('visible');
      return;
    }
    s.innerHTML = mate(html);
    s.classList.add('visible');
  }

  function crearNarrador(id) {
    const pausa = (ms) => esperar(ms, id);
    const anim = (ms, fn) => animar(ms, fn, id);
    /** Muestra el subtítulo y lo lee. Dura lo que tarde la voz, o un tiempo según el largo del texto. */
    const narrar = async (html, minimo) => {
      subtitulo(html);
      const plano = textoPlano(html);
      const base = minimo || 1600 + plano.length * 52;
      const t0 = performance.now();
      const hablo = await Sonido.decir(paraVoz(html));
      if (id !== historiaId) throw CANCELADO;
      const resto = (hablo ? 300 : base / ritmo) - (performance.now() - t0);
      if (resto > 0) await new Promise((ok) => setTimeout(ok, resto));
      if (id !== historiaId) throw CANCELADO;
    };
    return { pausa, anim, narrar, id };
  }

  function layout(clase) {
    const e = $('escenario');
    e.classList.remove('solo-visual', 'solo-pizarra', 'visual-chico');
    if (clase) e.classList.add(clase);
  }

  function pizarra(html) {
    $('pizarra').innerHTML = mate(html);
  }

  function agregar(html) {
    $('pizarra').insertAdjacentHTML('beforeend', mate(html));
    const p = $('pizarra');
    p.scrollTo({ top: p.scrollHeight, behavior: 'smooth' });
  }

  function hudZ(valor, etiqueta = 'VALOR DE Z') {
    const h = $('hud-z');
    if (valor === null) {
      h.classList.remove('visible');
      return;
    }
    h.querySelector('span').textContent = etiqueta;
    $('hud-z-valor').innerHTML = mate(E(valor));
    h.classList.add('visible');
  }

  function tipoVisual(s) {
    if (s.grafico) return '2d';
    if (s.poliedro && !s.poliedro.vacia) return '3d';
    return 'nada';
  }

  function usarVisual(s) {
    const t = tipoVisual(s);
    lienzo.modo = t;
    if (t === '2d') v2.usar(s.grafico);
    if (t === '3d') v3.usar(s.poliedro);
    return t;
  }

  const sentidoTxt = (s) => (s.sentido === 'max' ? 'maximizar' : 'minimizar');
  const nombreSub = (n) => E(n);   // la tipografía (x₁ en cursiva) la pone mate() al mostrarlo
  const punto = (s, xs) => '(' + xs.join(', ') + ')';
  const conFichas = (eq) => E(eq).replace(/\b([sea])(\d+)\b/g, (m, l) =>
    `<span class="ficha ${{ s: 'slack', e: 'surplus', a: 'art' }[l]}">${m}</span>`);

  function zTexto(p) {
    return p.zOrig.conM ? `Z′ = ${p.zOrig.txt}` : p.zOrig.txt;
  }

  // ====================================================================== tablero

  function tablaHTML(paso, op = {}) {
    const { header, rows, meta } = paso;
    const col = op.col ? meta.enter_col : null;
    const fila = op.fila ? meta.leave_row : null;
    const ult = rows.length - 1;
    let h = '<div class="tab-envoltura"><table class="tab"><thead><tr>';
    header.forEach((c, k) => (h += `<th class="${k === col ? 'col-entra' : ''}">${E(c)}</th>`));
    h += '</tr></thead><tbody>';
    rows.forEach((r, i) => {
      const cls = [i === ult ? 'dj' : '', i === fila ? 'fila-sale' : '', op.djFila && i === ult ? 'resaltada' : ''].join(' ');
      h += `<tr class="${cls}">`;
      r.forEach((c, k) => {
        const tc = [k === 0 ? 'etq' : '', k === col ? 'col-entra' : '',
          op.pivote && i === fila && k === col ? 'pivote' : '',
          op.brilla && i === ult && k === col ? 'brilla' : '', op.nuevo ? 'nuevo' : ''].join(' ');
        h += `<td class="${tc}">${E(c)}</td>`;
      });
      h += '</tr>';
    });
    return h + '</tbody></table></div>';
  }

  function razonesHTML(paso) {
    const vals = paso.razones.filter((r) => r.val !== null).map((r) => r.val);
    const max = Math.max(...vals, 1e-9);
    let h = '<div class="razones">';
    paso.razones.forEach((r, i) => {
      const cls = r.val === null ? 'na' : '';
      h += `<div class="razon ${cls}" data-i="${i}" data-w="${r.val === null ? 4 : Math.max(4, (r.val / max) * 100)}">
        <span>${E(r.var)}</span><div><div class="barra"></div></div>
        <span>${r.val === null ? `${E(r.num)}/${E(r.den)} —` : `${E(r.num)} / ${E(r.den)} = ${E(r.txt)}`}</span></div>`;
    });
    return h + '</div>';
  }

  function crecerRazones() {
    document.querySelectorAll('.razon').forEach((el) => {
      el.querySelector('.barra').style.width = el.dataset.w + '%';
    });
  }

  function marcarGanadora(paso) {
    document.querySelectorAll('.razon').forEach((el) => {
      const i = +el.dataset.i;
      const v = paso.razones[i].var;
      if (i === paso.filaSale) el.classList.add('gana');
      else if (paso.empate.includes(v)) el.classList.add('empate');
    });
  }

  // ====================================================================== capítulos

  async function cap1Problema(N) {
    const s = esc;
    const t = usarVisual(s);
    layout(t === 'nada' ? 'solo-pizarra' : '');
    hudZ(null);
    let h = `<p class="pz-titulo">El problema</p><div class="ecuacion oculta" id="eq-obj"><span class="r">Objetivo</span>${E(s.objetivo)}</div>`;
    s.restricciones.forEach((r, i) => (h += `<div class="ecuacion oculta" id="eq-r${i}">${E(r).replace(/^(R\d+):/, '<span class="r">$1</span>')}</div>`));
    h += `<div class="ecuacion oculta" id="eq-nn"><span class="r">y</span>${EL(s.vars, ', ')} ≥ 0</div>`;
    pizarra(h);
    const mostrar = (id, resaltar = true) => {
      document.querySelectorAll('.ecuacion').forEach((e) => e.classList.remove('resaltada'));
      const e = $(id);
      e.classList.remove('oculta');
      if (resaltar) e.classList.add('resaltada');
    };

    if (t === '2d') await N.anim(900, (k) => (v2.estado.ejes = k));
    if (t === '3d') await N.anim(900, (k) => (v3.estado.ejes = k));
    mostrar('eq-obj');
    await N.narrar(`Queremos <b>${sentidoTxt(s)}</b> ${E(s.objetivo.replace(/^(Max|Min) /, ''))}, con ${E(s.n)} variables y ${E(s.m)} restricciones.`);

    const frase = { '≤': 'Sirven los puntos del lado sombreado: los que no pasan el límite.',
      '≥': 'Sirven los puntos del lado sombreado: los que alcanzan al menos ese valor.',
      '=': 'Es una igualdad: solo sirven los puntos que están exactamente sobre la recta.' };
    for (let i = 0; i < s.m; i++) {
      mostrar(`eq-r${i}`);
      const r = s.restricciones[i];
      const signo = (r.match(/[≤≥=]/) || ['='])[0];
      if (t === '2d') {
        v2.estado.resaltar = i;
        await N.anim(900, (k) => (v2.estado.restr = i + k));
        v2.estado.semiplano = { i, alfa: 0 };
        N.anim(600, (k) => (v2.estado.semiplano.alfa = k)).catch(() => {});
        await N.narrar(`<b>${E(r.split(':')[0])}</b>: ${E(r.split(': ')[1])}. ${E(frase[signo])}`);
        await N.anim(400, (k) => (v2.estado.semiplano.alfa = 1 - k));
        v2.estado.semiplano = null;
      } else if (t === '3d') {
        v3.estado.carasVisibles = i + 1;
        v3.estado.resaltarCara = i;
        await N.anim(500, (k) => (v3.estado.caras = Math.max(v3.estado.caras, k)));
        await N.narrar(`<b>${E(r.split(':')[0])}</b>: ${E(r.split(': ')[1])}. Cada restricción es un plano que corta el espacio.`, 2600);
      } else {
        await N.narrar(`<b>${E(r.split(':')[0])}</b>: ${E(r.split(': ')[1])}.`, 2200);
      }
    }
    mostrar('eq-nn');
    if (t === '2d') {
      v2.estado.resaltar = -1;
      await N.anim(1100, (k) => (v2.estado.region = k));
      if (s.grafico.vacia) {
        v2.estado.textoCentro = { texto: 'Región factible vacía', alfa: 0 };
        await N.anim(700, (k) => (v2.estado.textoCentro.alfa = k));
        await N.narrar('No hay ningún punto que cumpla todas las restricciones a la vez: <b>la región factible está vacía</b>.');
        return;
      }
      await N.narrar(`Lo que cumple todas a la vez, con x₁ y x₂ no negativos, es la <b>región factible</b>${s.grafico.acotada ? '' : ', que en este caso <b>no tiene fin</b>'}.`);
      const red = s.grafico.rectas.map((r, i) => (r.redundante ? `R${i + 1}` : null)).filter(Boolean);
      if (red.length) await N.narrar(`${EL(red, ' y ')} ${red.length > 1 ? 'son redundantes' : 'es <b>redundante</b>'}: no toca la región, así que quitarla no cambia la solución.`);
      v2.estado.conZ = true;
      await N.anim(800, (k) => (v2.estado.vertices = k));
      await N.narrar('El óptimo de un problema lineal siempre está en un <b>vértice</b>. Aquí están todos, con su valor de Z. El simplex no los prueba todos: <b>salta de vértice en vértice, siempre mejorando</b>.');
    } else if (t === '3d') {
      v3.estado.resaltarCara = -1;
      v3.estado.carasVisibles = 99;
      await N.anim(900, (k) => {
        v3.estado.aristas = k;
        v3.estado.vertices = k;
      });
      await N.narrar(`Con tres variables la región factible es un <b>poliedro</b> de ${E(s.poliedro.vertices.length)} vértices. Arrastra para girarlo. El simplex camina por sus aristas, de vértice en vértice.`);
    } else {
      await N.narrar(`Con ${E(s.n)} variables no se puede dibujar: <b>el método gráfico no aplica</b>. El simplex funciona igual, en el tablero.`);
    }
  }

  async function cap2Estandar(N) {
    const s = esc;
    const t = usarVisual(s);
    layout('solo-pizarra');
    hudZ(null);
    pizarra(`<p class="pz-titulo">Forma estándar</p><p class="pz-grande">De desigualdades a ecuaciones</p>
      <div class="leyenda-fichas"><span><span class="ficha slack">s</span> holgura (≤)</span>
      <span><span class="ficha surplus">e</span> exceso (≥)</span><span><span class="ficha art">a</span> artificial (≥, =)</span></div>
      <div id="std"></div>`);
    await N.narrar('El simplex trabaja con <b>ecuaciones</b>, no con desigualdades. Por eso cada restricción recibe una variable nueva.');
    const dichos = new Set();
    for (let i = 0; i < s.m; i++) {
      const f = s.estandar.filas[i];
      let h = `<div class="tarjeta" id="std-${i}"><div class="ecuacion"><span class="r">R${i + 1}</span>${E(f.orig)}</div>`;
      if (f.flip) h += `<div class="flecha-tr">× (−1) porque el lado derecho es negativo ↓</div><div class="ecuacion"><span class="r">R${i + 1}</span>${E(f.normal)}</div>`;
      h += `<div class="flecha-tr">↓</div><div class="ecuacion"><span class="r">R${i + 1}</span>${conFichas(f.ecuacion)}</div></div>`;
      $('std').insertAdjacentHTML('beforeend', mate(h));
      $(`std-${i}`).scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      Sonido.toque(6 + i);
      const tipos = f.agregadas.map((a) => a.tipo);
      let texto = '';
      if (f.flip) texto += `R${i + 1} tiene lado derecho negativo: la multiplicamos por menos uno y el signo se invierte. `;
      const nom = (tp) => E(f.agregadas.find((a) => a.tipo === tp).nombre);
      if (tipos.includes('slack')) {
        texto += dichos.has('slack') ? `Holgura ${nom('slack')}.` :
          `Al ser ≤, sumamos la <b>holgura</b> ${nom('slack')}: mide cuánto le sobra a la restricción.`;
        dichos.add('slack');
      } else if (tipos.includes('surplus')) {
        texto += dichos.has('surplus') ? `Exceso ${nom('surplus')} y artificial ${nom('art')}.` :
          `Al ser ≥, restamos el <b>exceso</b> ${nom('surplus')}, lo que se pasa del mínimo. Pero así no hay una variable básica fácil para empezar, y agregamos la <b>artificial</b> ${nom('art')}.`;
        dichos.add('surplus');
      } else if (tipos.includes('art')) {
        texto += dichos.has('art=') ? `Artificial ${nom('art')}.` :
          `Es una igualdad: no le sobra ni le falta nada, pero necesitamos una variable para empezar, así que agregamos la <b>artificial</b> ${nom('art')}.`;
        dichos.add('art=');
      }
      await N.narrar(texto, dichos.size > 1 && texto.length < 40 ? 1500 : undefined);
    }
    agregar(`<div class="tarjeta"><h3>Función objetivo</h3><div class="ecuacion">${conFichas(s.estandar.lineas[0])}</div></div>`);
    if (s.estandar.tieneArt) {
      await N.narrar('Las artificiales no existen en el problema real. Para sacarlas, en la función objetivo cuestan <b>−M</b>: un castigo enorme.');
    } else if (s.sentido === 'min') {
      await N.narrar('Como es de minimización, maximizamos Z′ = −Z: es lo mismo, con el signo cambiado.');
    } else {
      await N.narrar('Las holguras no cambian la ganancia: en la función objetivo valen cero.');
    }
    const base0 = s.estandar.base0.join(', ');
    agregar(`<div class="tarjeta"><h3>Base inicial</h3><div class="ecuacion">${conFichas(base0)}</div></div>`);
    await N.narrar(`La base inicial la forman ${E(base0)}. Todas las variables originales arrancan en cero: el punto de partida es el <b>origen</b>${s.estandar.tieneArt ? ', que no cumple las restricciones; por eso hacen falta las artificiales' : ''}.`);
  }

  async function moverPunto(N, t, desde, hasta, factible, ms = 1400) {
    if (t === '2d') {
      const e = v2.estado;
      const a = [desde[0], desde[1]];
      const b = [hasta[0], hasta[1]];
      e.rastro.push(a.slice());
      await N.anim(ms, (k) => {
        e.punto.x = a[0] + (b[0] - a[0]) * k;
        e.punto.y = a[1] + (b[1] - a[1]) * k;
        e.rastro[e.rastro.length - 1] = [e.punto.x, e.punto.y];
        if (e.rastro.length === 1) e.rastro.unshift(a.slice());
      });
      e.rastro[e.rastro.length - 1] = b.slice();
      e.punto.factible = factible;
      e.pulsos.push({ x: b[0], y: b[1], t0: performance.now() });
    } else if (t === '3d') {
      const e = v3.estado;
      if (!e.rastro.length) e.rastro.push(desde.slice());
      e.rastro.push(desde.slice());
      await N.anim(ms, (k) => {
        e.punto.p = desde.map((v, i) => v + (hasta[i] - v) * k);
        e.rastro[e.rastro.length - 1] = e.punto.p.slice();
      });
      e.punto.factible = factible;
    }
  }

  function etiquetaPunto(s, p) {
    return `${punto(s, p.xs)}\n${p.zOrig.conM ? 'Z′ = ' + p.zOrig.txt : 'Z = ' + p.zOrig.txt}`;
  }

  async function cap3Viaje(N) {
    const s = esc;
    const t = usarVisual(s);
    layout(t === 'nada' ? 'solo-pizarra' : 'visual-chico');
    const P = s.pasos;
    if (t === '2d') {
      Object.assign(v2.estado, { ejes: 1, restr: s.m, region: 1, vertices: 1, conZ: false });
      v2.estado.punto = { x: P[0].x[0], y: P[0].x[1], alfa: 1, factible: P[0].factible, texto: etiquetaPunto(s, P[0]) };
    } else if (t === '3d') {
      Object.assign(v3.estado, { ejes: 1, caras: 1, aristas: 1, vertices: 1 });
      v3.estado.punto = { p: P[0].x.slice(), alfa: 1, factible: P[0].factible };
    }
    Sonido.intensidad(0.45);
    const compacto = P.length > 6;
    for (let k = 0; k < P.length; k++) {
      const p = P[k];
      const ultimo = k === P.length - 1;
      hudZ(zTexto(p), p.zOrig.conM ? 'VALOR DE Z′ (CON M)' : 'VALOR DE Z');
      pizarra(`<p class="pz-titulo">${E(s.metodo)} · iteración ${E(p.k)}</p><p class="pz-grande">Base: ${EL(p.base, ', ')}</p>${tablaHTML(p, { nuevo: k > 0 })}<div id="extra"></div>`);
      if (t === '2d') v2.estado.punto.texto = etiquetaPunto(s, p);
      if (t === '3d') v3.estado.punto.texto = etiquetaPunto(s, p);
      const breve = compacto && k >= 2 && !ultimo;
      if (k === 0) {
        await N.narrar(`Iteración 0. La base es ${EL(p.base, ', ')}: estamos en ${E(punto(s, p.xs))}, con ${p.zOrig.conM ? 'Z′ = ' : 'Z = '}${E(p.zOrig.txt)}${p.factible ? '' : ', fuera de la región'}.`);
      } else if (!breve) {
        await N.narrar(`Iteración ${E(p.k)}. Llegamos a ${E(punto(s, p.xs))}: ${p.zOrig.conM ? 'Z′ = ' : 'Z = '}${E(p.zOrig.txt)}.`, 2400);
      }

      if (p.entra && p.sale) {
        pizarra(`<p class="pz-titulo">${E(s.metodo)} · iteración ${E(p.k)}</p><p class="pz-grande">Base: ${EL(p.base, ', ')}</p>${tablaHTML(p, { col: true, djFila: true, brilla: true })}<div id="extra"></div>`);
        if (breve) {
          await N.narrar(`Iteración ${E(p.k)}: <span class="v">entra ${E(p.entra)}</span> (cj − zj = ${E(p.dj)}) y <span class="s">sale ${E(p.sale)}</span>, con pivote ${E(p.pivote)}.`, 2600);
        } else {
          await N.narrar(`Miramos la fila cj − zj. La mayor es la de ${E(p.entra)}: ${E(p.dj)}. <span class="v">Entra ${E(p.entra)}</span>${p.djM ? ', porque su parte de M es la más grande: es la que más rápido saca a las artificiales.' : ', porque es la que más mejora Z por cada unidad.'}`);
          $('extra').innerHTML = mate(`<p class="pz-titulo" style="margin-top:12px">Prueba de la razón mínima</p>${razonesHTML(p)}`);
          await N.pausa(80);
          crecerRazones();
          await N.pausa(900);
          marcarGanadora(p);
          const theta = p.razones[p.filaSale].txt;
          await N.narrar(`Prueba de la razón mínima: dividimos el lado derecho entre la columna de ${E(p.entra)}, solo donde es positiva. La menor es <b>${E(theta)}</b>: <span class="s">sale ${E(p.sale)}</span>, la restricción que se agota primero.`);
          if (p.empate.length) {
            await N.narrar(`¡Empate entre ${EL(p.empate, ' y ')}! Se elige la de menor índice. La próxima solución será <b>degenerada</b>: una variable básica quedará en cero.`);
          }
        }
        const tabla = $('pizarra').querySelector('.tab-envoltura');
        tabla.outerHTML = mate(tablaHTML(p, { col: true, fila: true, pivote: true }));
        Sonido.toque(8);
        if (!breve) await N.narrar(`El pivote es <b>${E(p.pivote)}</b>: dividimos su fila entre ${E(p.pivote)} y hacemos cero el resto de la columna.`, 2400);
        else await N.pausa(700);
        const sig = P[k + 1];
        Sonido.intensidad(0.8);
        await moverPunto(N, t, p.x, sig.x, sig.factible, breve ? 900 : 1500);
        Sonido.intensidad(0.45);
        Sonido.mejora(3 + k);
      } else if (ultimo) {
        await finalDelViaje(N, s, p, t);
      }
    }
  }

  async function finalDelViaje(N, s, p, t) {
    if (p.entra && !p.sale) {
      // no acotado
      pizarra(`<p class="pz-titulo">${E(s.metodo)} · iteración ${E(p.k)}</p><p class="pz-grande">Columna de ${E(p.entra)} sin positivos</p>${tablaHTML(p, { col: true, brilla: true })}`);
      await N.narrar(`Entra ${E(p.entra)}, pero <b>ningún elemento de su columna es positivo</b>: no hay razón mínima, nada la detiene.`);
      if (t === '2d' && s.rayo) {
        v2.estado.rayo = { desde: [p.x[0], p.x[1]], dir: s.rayo, t: 0 };
        await N.anim(1800, (k) => (v2.estado.rayo.t = k));
      }
      await N.narrar(`${E(p.entra)} puede crecer sin límite y Z con ella: <b>la solución es no acotada</b>.`);
      return;
    }
    pizarra(`<p class="pz-titulo">${E(s.metodo)} · tablero final</p><p class="pz-grande">Base: ${EL(p.base, ', ')}</p>${tablaHTML(p, { djFila: true })}`);
    if (s.estado === 'infeasible') {
      const arts = Object.entries(p.arts).filter(([, v]) => v > 0).map(([n]) => n).join(', ');
      await N.narrar(`Ningún cj − zj es positivo, pero la artificial <b>${E(arts)}</b> sigue en la base con valor positivo. No hay forma de cumplir todas las restricciones: <b>el problema es infactible</b>.`);
      if (t === '2d') {
        v2.estado.textoCentro = { texto: 'Sin solución factible', alfa: 0 };
        await N.anim(700, (k) => (v2.estado.textoCentro.alfa = k));
      }
      return;
    }
    await N.narrar('Ya <b>ningún cj − zj es positivo</b>: ninguna variable puede mejorar Z.');
    if (t === '2d') {
      v2.estado.lineaZ = { z: +s.z.split('/').reduce((a, b) => a / b), alfa: 0, texto: `Z = ${s.z}` };
      v2.estado.brilloVertice = [p.x[0], p.x[1]];
      await N.anim(900, (k) => (v2.estado.lineaZ.alfa = k));
    }
    Sonido.final();
    hudZ(s.z);
    const vars = s.vars.map((v, i) => `${nombreSub(v)} = ${E(s.x[i])}`).join(', ');
    await N.narrar(`<b>Solución óptima</b>: ${vars}, con <b>Z = ${E(s.z)}</b>${t === '2d' ? '. La recta de Z toca la región solo en ese vértice' : ''}.`);
    if (s.alternos.length) await N.narrar(`Además ${EL(s.altVars, ', ')} tiene cj − zj = 0: hay <b>óptimos múltiples</b>.`);
    if (s.degeneradas.length) await N.narrar(`Y ${EL(s.degeneradas, ', ')} es básica pero vale cero: la solución es <b>degenerada</b>.`);
  }

  /** Tabla de un bloque del simplex revisado (B⁻¹, multiplicadores o costos reducidos). */
  function bloqueHTML(b, resaltarFila, claseFila) {
    let h = `<p class="pz-titulo" style="margin-top:10px">${E(b.titulo)}</p><div class="tab-envoltura tab-chica"><table class="tab"><thead><tr>`;
    b.header.forEach((c) => (h += `<th>${E(c)}</th>`));
    h += '</tr></thead><tbody>';
    b.rows.forEach((r, i) => {
      h += `<tr class="${i === resaltarFila ? claseFila : ''}">`;
      r.forEach((c, k) => (h += `<td class="${k === 0 ? 'etq' : ''}">${E(c)}</td>`));
      h += '</tr>';
    });
    return h + '</tbody></table></div>';
  }

  function comparacionHTML(s) {
    const a = s.pasos;
    const b = s.revisado.pasos;
    const n = Math.max(a.length, b.length);
    let h = '<div class="tab-envoltura tab-chica"><table class="tab"><thead><tr><th>Iter.</th><th>Gran M: entra</th><th>sale</th><th>Z</th><th>Revisado: entra</th><th>sale</th><th>Z</th></tr></thead><tbody>';
    for (let k = 0; k < n; k++) {
      const p = a[k] || {};
      const q = b[k] || {};
      h += `<tr><td class="etq">${k}</td><td>${E(p.entra || '—')}</td><td>${E(p.sale || '—')}</td><td>${p.zOrig ? E(zTexto(p)) : ''}</td>`
        + `<td>${E(q.entra || '—')}</td><td>${E(q.sale || '—')}</td><td>${q.zOrig ? E(zTexto(q)) : ''}</td></tr>`;
    }
    return h + '</tbody></table></div>';
  }

  async function capRevisado(N) {
    const s = esc;
    const R = s.revisado;
    const t = usarVisual(s);
    layout(t === 'nada' ? 'solo-pizarra' : 'visual-chico');
    const P = R.pasos;
    if (t === '2d') {
      Object.assign(v2.estado, { ejes: 1, restr: s.m, region: 1, vertices: 1, conZ: false });
      v2.estado.rastro = [];
      v2.estado.punto = { x: P[0].x[0], y: P[0].x[1], alfa: 1, factible: P[0].factible, texto: etiquetaPunto(s, P[0]) };
    } else if (t === '3d') {
      Object.assign(v3.estado, { ejes: 1, caras: 1, aristas: 1, vertices: 1 });
      v3.estado.rastro = [];
      v3.estado.punto = { p: P[0].x.slice(), alfa: 1, factible: P[0].factible };
    }
    const compacto = P.length > 5;
    for (let k = 0; k < P.length; k++) {
      const p = P[k];
      const [bInv, mult, costos] = p.bloques;
      const breve = compacto && k >= 2 && k < P.length - 1;
      hudZ(zTexto(p), p.zOrig.conM ? 'VALOR DE Z′ (CON M)' : 'VALOR DE Z');
      if (t === '2d') v2.estado.punto.texto = etiquetaPunto(s, p);
      if (t === '3d') v3.estado.punto.texto = etiquetaPunto(s, p);
      const cabeza = `<p class="pz-titulo">Simplex revisado · iteración ${E(p.k)}</p><p class="pz-grande">Base: ${EL(p.base)}</p>`;
      pizarra(cabeza + bloqueHTML(bInv, -1, ''));
      if (k === 0) {
        await N.narrar('El <b>simplex revisado</b> resuelve el mismo problema sin cargar todo el tablero. Solo guarda <b>B⁻¹</b>, la inversa de la matriz de la base.');
        await N.narrar(`Al inicio la base es ${EL(p.base)}: sus columnas forman la identidad, así que B⁻¹ también es la identidad, y x<sub>B</sub> = B⁻¹·b es el lado derecho.`);
      } else if (!breve) {
        await N.narrar(`Iteración ${E(p.k)}. Con la nueva B⁻¹, x<sub>B</sub> = B⁻¹·b da el punto ${E(punto(s, p.xs))}.`, 2400);
      }
      agregar(bloqueHTML(mult, -1, '') + bloqueHTML(costos, p.entra ? costos.meta.enter_row : -1, 'resaltada'));
      if (!p.entra) {
        await N.narrar(R.estado === 'infeasible'
          ? 'Ningún costo reducido es positivo, pero queda una artificial positiva en la base: <b>el problema es infactible</b>, igual que con la Gran M.'
          : 'Ningún costo reducido es positivo: <b>llegamos al óptimo</b>.');
        break;
      }
      if (breve) {
        await N.narrar(`Iteración ${E(p.k)}: <span class="v">entra ${E(p.entra)}</span> (cj − zj = ${E(p.dj)})${p.sale ? ` y <span class="s">sale ${E(p.sale)}</span>` : ''}.`, 2400);
      } else {
        await N.narrar(`Calcula los multiplicadores <b>y = c<sub>B</sub>·B⁻¹</b> y con ellos el costo reducido de cada no básica: cj − y·aj. El mayor es el de ${E(p.entra)}, ${E(p.dj)}: <span class="v">entra ${E(p.entra)}</span>.`);
      }
      if (!p.sale) {
        pizarra(cabeza + bloqueHTML(bInv, -1, ''));
        await N.narrar(`La dirección α = B⁻¹·a de ${E(p.entra)} no tiene componentes positivas: no hay razón mínima y <b>la solución es no acotada</b>.`);
        break;
      }
      pizarra(cabeza + bloqueHTML(bInv, bInv.meta.leave_row, 'fila-sale'));
      if (!breve) {
        await N.narrar(`Solo para la que entra calcula su columna <b>α = B⁻¹·a</b>. La razón mínima x<sub>B</sub>/α es ${E(p.theta)}: <span class="s">sale ${E(p.sale)}</span>. Pivoteando con ${E(p.pivote)} se actualiza B⁻¹.`);
      } else {
        await N.pausa(900);
      }
      const sig = P[k + 1];
      await moverPunto(N, t, p.x, sig.x, sig.factible, breve ? 900 : 1300);
      Sonido.mejora(3 + k);
    }
    layout('solo-pizarra');
    pizarra(`<p class="pz-titulo">Gran M y simplex revisado</p><p class="pz-grande">${R.iguales ? 'Mismo camino, mismo resultado' : 'Los dos métodos difieren'}</p>${comparacionHTML(s)}`);
    await N.narrar(R.iguales
      ? `Los dos métodos usan la misma regla para elegir quién entra y quién sale, así que recorren <b>las mismas ${P.length - 1} iteraciones</b> y llegan al mismo resultado. La diferencia está en el trabajo: el tablero actualiza toda la matriz, el revisado solo B⁻¹.`
      : 'En este problema los dos métodos no siguieron exactamente el mismo camino; la tabla muestra en qué iteración se separan.');
  }

  async function cap4GranM(N) {
    let s = esc;
    if (!s.estandar.tieneArt) {
      s = D.casos.artificiales;
      layout('solo-pizarra');
      pizarra('<p class="pz-titulo">La Gran M</p>');
      await N.narrar('Este problema no necesitó variables artificiales. Veamos el <b>ejemplo 2 del enunciado</b>, que sí las usa.');
    }
    const t = usarVisual(s);
    layout(t === 'nada' ? 'solo-pizarra' : '');
    const arts = s.estandar.nombres.filter((n, i) => s.estandar.tipos[i] === 'art');
    const max = Math.max(1e-9, ...s.pasos.flatMap((p) => Object.values(p.arts)));
    let h = `<p class="pz-titulo">La Gran M</p><p class="pz-grande">${E(s.objetivo)}</p><div class="barras-art">`;
    arts.forEach((a) => (h += `<div class="barra-art"><span class="v" id="v-${E(a)}"></span><div class="b" id="b-${E(a)}" style="height:0"></div><span class="n">${E(a)}</span></div>`));
    h += '</div><p class="interp" id="gm-iter"></p>';
    pizarra(h);
    const pintarBarras = (p) => {
      arts.forEach((a) => {
        const v = p.arts[a] || 0;
        $(`b-${a}`).style.height = (v / max) * 85 + '%';
        $(`v-${a}`).textContent = v ? (Math.round(v * 1000) / 1000).toString() : '0';
      });
      $('gm-iter').innerHTML = mate(`Iteración ${E(p.k)} · ${p.zOrig.conM ? 'Z′ = ' : 'Z = '}<b>${E(p.zOrig.txt)}</b>`);
    };
    if (t === '2d') {
      Object.assign(v2.estado, { ejes: 1, restr: s.m, region: 1, vertices: 1 });
      v2.estado.punto = { x: s.pasos[0].x[0], y: s.pasos[0].x[1], alfa: 1, factible: s.pasos[0].factible, texto: 'inicio' };
    }
    hudZ(zTexto(s.pasos[0]), 'VALOR DE Z′');
    await N.pausa(200);
    pintarBarras(s.pasos[0]);
    await N.narrar(`Las artificiales (${EL(arts, ', ')}) son <b>muletas</b>: dan una base para empezar, pero no son parte del problema real.`);
    await N.narrar('Mientras alguna sea positiva, el punto <span class="s">no cumple las restricciones originales</span>. En la función objetivo cuestan −M, así que el simplex las saca primero.');
    for (let k = 1; k < s.pasos.length; k++) {
      const a = s.pasos[k - 1];
      const p = s.pasos[k];
      if (t === '2d') await moverPunto(N, t, a.x, p.x, p.factible, 1300);
      pintarBarras(p);
      hudZ(zTexto(p), p.zOrig.conM ? 'VALOR DE Z′' : 'VALOR DE Z');
      if (t === '2d') v2.estado.punto.texto = etiquetaPunto(s, p);
      Sonido.mejora(4 + k);
      const quedan = Object.entries(p.arts).filter(([, v]) => v > 0).map(([n]) => n);
      if (a.sale && arts.includes(a.sale)) {
        await N.narrar(`Iteración ${E(p.k)}: <span class="s">sale ${E(a.sale)}</span>. ${quedan.length ? `Todavía queda ${EL(quedan, ', ')}.` : '<b>Ya no queda ninguna artificial</b>: el punto entró a la región factible.'}`, 2600);
      } else {
        await N.narrar(`Iteración ${E(p.k)}: ya dentro de la región, el simplex sigue mejorando Z.`, 2200);
      }
    }
    if (s.estado === 'infeasible') {
      await N.narrar('Una artificial no pudo salir: no existe ningún punto que cumpla todas las restricciones. Así detecta la Gran M un problema <b>infactible</b>.');
    } else {
      await N.narrar('En la aplicación M no tiene un valor fijo: cada costo se guarda como <b>a + b·M</b> y se compara primero la parte de M. Así no hay que adivinar qué tan grande debe ser.');
    }
  }

  async function cap5Sensibilidad(N) {
    const s = esc;
    hudZ(null);
    if (s.estado !== 'optimal') {
      layout('solo-pizarra');
      pizarra('<p class="pz-titulo">Análisis de sensibilidad</p><p class="pz-grande">No aplica</p>');
      await N.narrar('Este problema no tiene solución óptima, así que <b>no hay análisis de sensibilidad</b>. Se hace sobre el tablero óptimo.');
      return;
    }
    const S = s.sensibilidad;
    const A = S.animacion;
    const tabla = () => {
      let h = '<div class="tab-chica"><table class="tab"><thead><tr><th>Restricción</th><th>LD</th><th>Precio sombra</th><th>Rango del LD</th></tr></thead><tbody>';
      S.restr.forEach((r, i) => (h += `<tr class="${A && A.restr === i ? 'resaltada' : ''}"><td class="etq">${E(r.nombre)}</td><td>${E(r.ld)}</td><td>${E(r.precio)}</td><td>[${E(r.lo)} ; ${E(r.hi)}]</td></tr>`));
      h += '</tbody></table><table class="tab"><thead><tr><th>Variable</th><th>Valor</th><th>Costo reducido</th><th>Rango del coeficiente</th></tr></thead><tbody>';
      S.vars.forEach((v) => (h += `<tr><td class="etq">${E(v.nombre)}${v.basica ? '' : ' (no básica)'}</td><td>${E(v.valor)}</td><td>${E(v.reducido)}</td><td>[${E(v.lo)} ; ${E(v.hi)}]</td></tr>`));
      return h + '</tbody></table></div>';
    };
    const t = usarVisual(s);
    if (A && t === '2d') {
      layout('');
      pizarra(`<p class="pz-titulo">Análisis de sensibilidad</p><p class="pz-grande">¿Y si cambia un recurso?</p>${tabla()}<p class="interp" id="sens-vivo"></p>`);
      Object.assign(v2.estado, { ejes: 1, restr: s.m, region: 1, vertices: 0, resaltar: A.restr });
      const fr = A.frames;
      let i0 = 0;
      fr.forEach((f, i) => { if (Math.abs(f.b - A.b0) < Math.abs(fr[i0].b - A.b0)) i0 = i; });
      const aplicar = (f) => {
        v2.estado.bCambio = { i: A.restr, b: f.b };
        if (f.x) {
          v2.estado.punto = { x: f.x[0], y: f.x[1], alfa: 1, factible: f.dentro, texto: `Z = ${Dibujo.bonito(f.z)}` };
          v2.estado.lineaZ = { z: f.z, alfa: 0.8 };
        } else {
          v2.estado.punto = null;
          v2.estado.lineaZ = null;
        }
        hudZ(f.bs, `LADO DERECHO DE R${A.restr + 1}`);
        $('sens-vivo').innerHTML = mate(f.x
          ? `R${A.restr + 1}: b = <b>${E(f.bs)}</b> → Z = <b>${Dibujo.bonito(f.z)}</b> · ${f.dentro ? '<span style="color:var(--verde)">dentro del rango</span>' : '<span style="color:var(--salmon)">fuera del rango: cambia la base</span>'}`
          : `R${A.restr + 1}: b = <b>${E(f.bs)}</b> → ${f.estado === 'infeasible' ? 'infactible' : 'sin óptimo'}`);
      };
      aplicar(fr[i0]);
      await N.narrar(`El <b>precio sombra</b> dice cuánto cambia Z por cada unidad extra de un lado derecho. Movamos el de <b>R${A.restr + 1}</b>, que hoy vale ${E(A.b0s)}.`);
      const recorrer = async (desde, hasta, ms) => {
        const n = Math.abs(hasta - desde);
        if (!n) return;
        let ult = -1;
        await N.anim(ms, (k) => {
          const i = Math.round(desde + (hasta - desde) * k);
          if (i !== ult) {
            aplicar(fr[i]);
            ult = i;
          }
        });
      };
      Sonido.musicaActiva(true);
      await recorrer(i0, fr.length - 1, 4200);
      await N.narrar(`Mientras b esté entre <b>${E(A.lo)}</b> y <b>${E(A.hi)}</b>, cada unidad adicional cambia Z en <b>${E(A.precio)}</b>. Fuera de ese rango cambia la base y el precio sombra deja de valer.`);
      await recorrer(fr.length - 1, 0, 5200);
      await recorrer(0, i0, 2600);
      v2.estado.bCambio = null;
    } else {
      layout('solo-pizarra');
      pizarra(`<p class="pz-titulo">Análisis de sensibilidad</p><p class="pz-grande">Precios sombra y rangos</p>${tabla()}`);
      await N.narrar('El <b>precio sombra</b> dice cuánto cambia Z por cada unidad extra de un lado derecho, dentro de su rango.');
    }
    const r = S.restr.find((x) => x.precio !== '0');
    if (r) await N.narrar(`Por ejemplo, si ${E(r.nombre)} pasa de ${E(r.ld)} a una unidad más, Z cambia en <b>${E(r.precio)}</b>, válido mientras su lado derecho esté entre ${E(r.lo)} y ${E(r.hi)}.`);
    const libre = S.restr.find((x) => x.precio === '0' && !x.activa);
    if (libre) await N.narrar(`${E(libre.nombre)} tiene precio sombra 0: le sobra holgura, así que más recurso no sirve.`);
    const nb = S.vars.find((v) => !v.basica);
    if (nb) await N.narrar(`${E(nb.nombre)} vale cero. Su <b>costo reducido</b>, ${E(nb.reducido)}, es lo que cambiaría Z si la obligáramos a tomar una unidad.`);
    const b = S.vars.find((v) => v.basica);
    if (b) await N.narrar(`Y el coeficiente de ${E(b.nombre)} puede moverse entre ${E(b.lo)} y ${E(b.hi)} sin que cambie la solución óptima.`);
  }

  async function cap6Casos(N) {
    layout('');
    hudZ(null);
    const C = D.casos;
    const lista = [
      ['infactible', 'Infactible', 'Restricciones imposibles de cumplir a la vez'],
      ['noAcotado', 'No acotado', 'Z puede crecer sin límite'],
      ['multiples', 'Óptimos múltiples', 'Todo un segmento es óptimo'],
      ['degenerado', 'Degenerado', 'Una básica vale cero'],
    ];
    let h = '<p class="pz-titulo">Casos especiales</p><p class="pz-grande">Cuando no hay una única respuesta</p><div class="casos">';
    lista.forEach(([k, n, d]) => (h += `<div class="caso" id="caso-${k}"><b>${E(n)}</b><small>${E(d)}</small></div>`));
    h += '</div><div id="caso-detalle"></div>';
    pizarra(h);
    await N.narrar('La aplicación reconoce cuatro situaciones especiales y las explica con un mensaje claro, <b>nunca con un error</b>.');
    for (const [k] of lista) {
      document.querySelectorAll('.caso').forEach((e) => e.classList.remove('activo'));
      $(`caso-${k}`).classList.add('activo');
      const s = C[k];
      usarVisual(s);
      const e = v2.estado;
      $('caso-detalle').innerHTML = mate(`<div class="tarjeta"><div class="ecuacion" style="font-size:17px">${E(s.objetivo)}</div>${s.restricciones.map((r) => `<div class="ecuacion" style="font-size:17px">${E(r)}</div>`).join('')}</div>`);
      Sonido.barrido(true);
      e.ejes = 1;
      await N.anim(1000, (q) => (e.restr = q * s.m));
      if (k === 'infactible') {
        for (let i = 0; i < s.m; i++) {
          e.semiplano = { i, alfa: 0 };
          await N.anim(500, (q) => (e.semiplano.alfa = q));
          await N.pausa(500);
        }
        e.semiplano = null;
        e.textoCentro = { texto: '∅  Región vacía', alfa: 0 };
        await N.anim(700, (q) => (e.textoCentro.alfa = q));
        await N.narrar(`<b>Infactible</b>: ${s.restricciones.map((r) => r.split(': ')[1]).join(' y ')} no se pueden cumplir a la vez. En el simplex, una artificial queda positiva al final.`);
      } else if (k === 'noAcotado') {
        await N.anim(700, (q) => (e.region = q));
        const last = s.pasos[s.pasos.length - 1];
        e.punto = { x: last.x[0], y: last.x[1], alfa: 1, factible: true };
        e.rayo = { desde: [last.x[0], last.x[1]], dir: s.rayo, t: 0 };
        await N.anim(2000, (q) => (e.rayo.t = q));
        await N.narrar(`<b>No acotado</b>: la región se abre hacia el infinito en la dirección en que Z mejora. En el tablero, la columna de ${E(s.noAcotadaVar)} no tiene positivos: no hay razón mínima.`);
      } else if (k === 'multiples') {
        await N.anim(700, (q) => (e.region = q));
        e.conZ = true;
        e.vertices = 1;
        const opt = s.grafico.vertices.filter((v) => v.opt);
        e.lineaZ = { z: opt[0].z, alfa: 0, texto: `Z = ${opt[0].zs}` };
        await N.anim(900, (q) => (e.lineaZ.alfa = q));
        e.segmento = { a: [opt[0].x, opt[0].y], b: [opt[opt.length - 1].x, opt[opt.length - 1].y], alfa: 0 };
        await N.anim(900, (q) => (e.segmento.alfa = q));
        await N.narrar(`<b>Óptimos múltiples</b>: la recta de Z es paralela a un borde, así que todo el segmento entre (${E(opt[0].xs)}, ${E(opt[0].ys)}) y (${E(opt[opt.length - 1].xs)}, ${E(opt[opt.length - 1].ys)}) da Z = ${E(opt[0].zs)}. En el tablero final, una variable no básica tiene cj − zj = 0.`);
      } else if (k === 'degenerado') {
        await N.anim(700, (q) => (e.region = q));
        e.vertices = 1;
        const opt = s.grafico.vertices.find((v) => v.opt);
        e.brilloVertice = [opt.x, opt.y];
        for (let r = 0; r < 3; r++) {
          e.pulsos.push({ x: opt.x, y: opt.y, t0: performance.now(), color: '#f28b7f' });
          await N.pausa(450);
        }
        await N.narrar(`<b>Degenerado</b>: en (${E(opt.xs)}, ${E(opt.ys)}) se cruzan más rectas de las necesarias. En la razón mínima hay empate, y ${EL(s.degeneradas, ', ')} queda en la base valiendo cero.`);
      }
      $(`caso-${k}`).classList.remove('activo');
      $(`caso-${k}`).classList.add('hecho');
    }
  }

  async function cap7Resultado(N) {
    const s = esc;
    const t = usarVisual(s);
    hudZ(null);
    layout(t === '2d' ? 'visual-chico' : 'solo-pizarra');
    if (t === '2d') {
      Object.assign(v2.estado, { ejes: 1, restr: s.m, region: 1, vertices: 1, conZ: true });
      v2.estado.rastro = s.pasos.filter((p) => p.factible).map((p) => [p.x[0], p.x[1]]);
      if (s.x) {
        const x = s.x.map((v) => +v.split('/').reduce((a, b) => a / b));
        v2.estado.punto = { x: x[0], y: x[1], alfa: 1, factible: true, texto: `Óptimo\nZ = ${s.z}` };
        v2.estado.lineaZ = { z: +s.z.split('/').reduce((a, b) => a / b), alfa: 0.9 };
      }
    }
    const it = s.pasos.length - 1;
    let h = '<p class="pz-titulo">Resultado</p>';
    if (s.estado === 'optimal') {
      h += `<span class="estado ok">Solución óptima</span><div class="cifra-grande">Z = ${E(s.z)}</div>
        <div class="vars">${s.vars.map((v, i) => `<div>${nombreSub(v)} = <b>${E(s.x[i])}</b></div>`).join('')}</div>
        <div class="tarjeta"><h3>Holgura o exceso</h3>${s.holguras.map((x, i) => `<div class="interp">R${i + 1}: ${E(x.tipo)} = <b>${E(x.valor)}</b>${x.valor === '0' ? ' (activa)' : ''}</div>`).join('')}</div>`;
    } else {
      h += `<span class="estado ${s.estado === 'infeasible' ? 'mal' : 'aviso'}">${s.estado === 'infeasible' ? 'Problema infactible' : 'Solución no acotada'}</span>`;
    }
    if (s.mensajes.length) h += `<div class="tarjeta"><h3>Mensajes de la aplicación</h3>${s.mensajes.map((m) => `<div class="interp">${E(m)}</div>`).join('')}</div>`;
    h += `<div class="tarjeta"><h3>Cómo se resolvió</h3><div class="interp">${E(s.metodo)} · <b>${it}</b> iteración(es) · fracciones exactas</div></div>`;
    pizarra(h);
    if (s.estado === 'optimal') {
      Sonido.final();
      await N.narrar(`En resumen: ${s.vars.map((v, i) => `${nombreSub(v)} = ${E(s.x[i])}`).join(', ')}, con <b>Z = ${E(s.z)}</b>, en ${it} iteraciones.`);
    } else {
      await N.narrar(`En resumen: ${s.estado === 'infeasible' ? 'el problema no tiene solución factible' : 'la solución es no acotada'}, y la aplicación lo informa con un mensaje claro.`);
    }
    await N.narrar(s.revisado.iguales
      ? 'Lo resolvimos con los dos métodos, la Gran M en tablero y el simplex revisado con B⁻¹, y <b>coinciden en cada iteración</b>.'
      : 'Lo resolvimos con los dos métodos, la Gran M en tablero y el simplex revisado con B⁻¹; la aplicación muestra dónde difieren.');
    await N.narrar('Todo lo que vieron lo calculó nuestro propio motor, con fracciones exactas. <b>¡Gracias!</b>');
  }

  const CAPITULOS = [
    { titulo: 'El problema', corto: 'Problema', fn: cap1Problema },
    { titulo: 'Forma estándar', corto: 'Estándar', fn: cap2Estandar },
    { titulo: 'El viaje del simplex (Gran M en tablero)', corto: 'Tablero', fn: cap3Viaje },
    { titulo: 'Simplex revisado', corto: 'Revisado', fn: capRevisado },
    { titulo: 'La Gran M', corto: 'Gran M', fn: cap4GranM },
    { titulo: 'Sensibilidad', corto: 'Sensibilidad', fn: cap5Sensibilidad },
    { titulo: 'Casos especiales', corto: 'Casos', fn: cap6Casos },
    { titulo: 'Resultado', corto: 'Resultado', fn: cap7Resultado },
  ];

  // ====================================================================== reproducción

  function mostrarCapitulo(k, terminado) {
    const el = $('hud-capitulo');
    const sig = k + 1 < CAPITULOS.length ? 'Av Pág: siguiente capítulo' : 'Fin · Av Pág: volver a empezar';
    el.innerHTML = `<span>CAPÍTULO ${k + 1} DE ${E(CAPITULOS.length)}</span><b>${E(CAPITULOS[k].titulo)}</b>${terminado ? `<small>${E(sig)}</small>` : ''}`;
    el.classList.add('visible');
    document.querySelectorAll('#capitulos button').forEach((b, i) => b.classList.toggle('activo', i === k));
  }

  function cancelar() {
    historiaId++;
    Sonido.callar();
  }

  async function reproducir(desde, hasta) {
    cancelar();
    const id = historiaId;
    $('portada').classList.add('oculta');
    setTimeout(() => {
      if ($('portada').classList.contains('oculta')) $('portada').style.display = 'none';
    }, 1100);
    document.body.classList.add('cine');
    Sonido.musicaActiva(true);
    Sonido.intensidad(0.35);
    const N = crearNarrador(id);
    try {
      for (let k = desde; k <= hasta; k++) {
        capituloActual = k;
        mostrarCapitulo(k, false);
        subtitulo('');
        Sonido.barrido(true);
        await CAPITULOS[k].fn(N);
        if (k < hasta) await N.pausa(700);
      }
      mostrarCapitulo(hasta, true);
      Sonido.musicaActiva(false);
      setTimeout(() => {
        if (id === historiaId) subtitulo('');
      }, 2500);
    } catch (err) {
      if (err !== CANCELADO) {
        console.error(err);
        subtitulo('Ocurrió un error en la animación: ' + E(err.message || err));
      }
    }
  }

  const irA = (k) => reproducir(Math.max(0, Math.min(CAPITULOS.length - 1, k)), Math.max(0, Math.min(CAPITULOS.length - 1, k)));
  const siguiente = () => irA(capituloActual + 1 >= CAPITULOS.length ? 0 : capituloActual + 1);
  const anterior = () => irA(Math.max(0, capituloActual - 1));
  const todo = () => reproducir(0, CAPITULOS.length - 1);

  // ====================================================================== panel

  function elegirEscena(s) {
    cancelar();
    esc = s;
    capituloActual = -1;
    $('info-problema').innerHTML = mate(EL([s.objetivo, ...s.restricciones], '\n'));
    $('portada-problema').innerHTML = mate(`${E(s.nombre)}: ${E(s.objetivo)}`);
    $('portada').style.display = '';
    $('portada').classList.remove('oculta');
    $('hud-capitulo').classList.remove('visible');
    hudZ(null);
    subtitulo('');
    lienzo.modo = 'nada';
    pizarra('');
    layout('solo-visual');
  }

  function iniciarPanel() {
    const caps = $('capitulos');
    CAPITULOS.forEach((c, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = `<b>${i + 1}</b>${c.corto}`;
      b.onclick = () => irA(i);
      caps.appendChild(b);
    });
    $('btn-todo').onclick = todo;

    const sel = $('sel-problema');
    const opciones = [['principal', D.principal.nombre + ' (exportado)']];
    Object.keys(D.ejemplos).forEach((k) => opciones.push([k, 'Ejemplo ' + k]));
    // si el principal es uno de los ejemplos, no se repite
    const igual = Object.entries(D.ejemplos).find(([, v]) => JSON.stringify(v.restricciones) === JSON.stringify(D.principal.restricciones) && v.objetivo === D.principal.objetivo);
    opciones.forEach(([v, t]) => {
      if (igual && v === 'principal') return;
      const o = document.createElement('option');
      o.value = v;
      o.textContent = t;
      sel.appendChild(o);
    });
    if (igual) sel.value = igual[0];
    sel.onchange = () => elegirEscena(sel.value === 'principal' ? D.principal : D.ejemplos[sel.value]);

    // sonido
    const aplicar = () => Sonido.configurar({
      voz: $('chk-voz').checked, musica: $('chk-musica').checked, efectos: $('chk-efectos').checked,
      volumen: +$('r-volumen').value,
    });
    ['chk-voz', 'chk-musica', 'chk-efectos', 'r-volumen'].forEach((id) => ($(id).oninput = aplicar));
    $('r-ritmo').oninput = () => (ritmo = +$('r-ritmo').value);
    const llenarVoces = () => {
      const sv = $('sel-voz');
      const actual = Sonido.vozActual();
      sv.innerHTML = '';
      const recomendada = Sonido.recomendada();
      Sonido.voces().forEach((v) => {
        const o = document.createElement('option');
        o.value = v.name;
        o.textContent = v === recomendada
          ? `${Sonido.nombreCorto(v)} · Microsoft Edge (recomendada)`
          : `${Sonido.nombreCorto(v)} (${v.lang})`;
        if (actual && v.name === actual.name) o.selected = true;
        sv.appendChild(o);
      });
      if (!sv.options.length) sv.innerHTML = '<option>Sin voces en español (solo subtítulos)</option>';
      $('nota-voz').textContent = recomendada ? ''
        : 'Para escuchar la voz recomendada (Salomé, voz de mujer) abre la presentación en Microsoft Edge.';
    };
    llenarVoces();
    Sonido.alCambiarVoces(llenarVoces);
    $('sel-voz').onchange = () => Sonido.elegirVoz($('sel-voz').value);
    Sonido.alCambiarVozActiva((antes, ahora) => {
      const a = $('aviso-voz');
      a.textContent = `La voz ${Sonido.nombreCorto(antes)} no está disponible ahora; se usa ${ahora ? Sonido.nombreCorto(ahora) : 'solo subtítulos'}.`;
      a.classList.add('visible');
      setTimeout(() => a.classList.remove('visible'), 6000);
      llenarVoces();
    });
  }

  // ====================================================================== teclado y portada

  let desbloqueado = false;
  function desbloquear() {
    if (desbloqueado) return;
    desbloqueado = true;
    Sonido.desbloquear();
    Sonido.probarVoz();
  }

  document.addEventListener('keydown', (ev) => {
    if (ev.target.tagName === 'SELECT' || ev.target.tagName === 'INPUT') return;
    desbloquear();
    const k = ev.key;
    if (k === 'PageDown' || k === 'ArrowRight' || k === ' ') {
      ev.preventDefault();
      siguiente();
    } else if (k === 'PageUp' || k === 'ArrowLeft') {
      ev.preventDefault();
      anterior();
    } else if (k === 'h' || k === 'H') todo();
    else if (k === 'f' || k === 'F') {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    } else if (k === 'm' || k === 'M') {
      const off = Sonido.preferencias().volumen > 0;
      $('r-volumen').value = off ? 0 : 0.8;
      Sonido.configurar({ volumen: off ? 0 : 0.8 });
      if (off) Sonido.callar();
    } else if (k === 'c' || k === 'C') document.body.classList.toggle('cine');
    else if (k === 'Escape') document.body.classList.remove('cine');
    else if (/^[1-9]$/.test(k) && +k <= CAPITULOS.length) irA(+k - 1);
  });
  document.addEventListener('pointerdown', desbloquear);
  $('portada').addEventListener('click', () => {
    desbloquear();
    irA(0);
  });

  // fondo animado de la portada: rectas que giran y forman polígonos
  (function fondoPortada() {
    const c = $('portada-fondo');
    const ctx = c.getContext('2d');
    const rectas = Array.from({ length: 9 }, (_, i) => ({ a: (i / 9) * Math.PI, v: 0.00005 + Math.random() * 0.0001, d: 0.15 + Math.random() * 0.3, col: Dibujo.COLORES[i % 8] }));
    const pinta = (t) => {
      if (!$('portada').classList.contains('oculta')) {
        const W = (c.width = c.clientWidth);
        const H = (c.height = c.clientHeight);
        ctx.clearRect(0, 0, W, H);
        ctx.lineWidth = 1.5;
        for (const r of rectas) {
          const a = r.a + t * r.v;
          const nx = Math.cos(a), ny = Math.sin(a);
          const cx = W / 2 + nx * r.d * W * 0.5, cy = H / 2 + ny * r.d * H * 0.5;
          ctx.strokeStyle = r.col;
          ctx.globalAlpha = 0.5;
          ctx.beginPath();
          ctx.moveTo(cx - ny * W, cy + nx * W);
          ctx.lineTo(cx + ny * W, cy - nx * W);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
      requestAnimationFrame(pinta);
    };
    requestAnimationFrame(pinta);
  })();

  iniciarPanel();
  elegirEscena(esc);
  const sel = $('sel-problema');
  if (sel.value && sel.value !== 'principal' && D.ejemplos[sel.value]) esc = D.ejemplos[sel.value];

  // Para pruebas y grabación: #cap=3&prob=2&ritmo=3 abre directamente un capítulo.
  const hash = new URLSearchParams(location.hash.slice(1));
  if (hash.get('prob')) {
    const k = Object.keys(D.ejemplos)[+hash.get('prob') - 1];
    if (k) {
      sel.value = k;
      elegirEscena(D.ejemplos[k]);
    }
  }
  if (hash.has('prueba')) document.body.classList.add('prueba');
  if (hash.get('ritmo')) ritmo = +hash.get('ritmo');
  if (hash.get('cap')) irA(+hash.get('cap') - 1);
  window.Presentacion = { irA, todo, CAPITULOS, paraVoz };
})();
