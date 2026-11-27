/*
 * Dibujo de la presentación en un único <canvas>:
 *  - Vista2D: región factible, restricciones, vértices, punto del simplex, recta de Z.
 *  - Vista3D: poliedro factible de 3 variables que se puede girar con el mouse.
 * Las escenas (app.js) solo cambian el objeto `estado`; aquí se pinta cada cuadro.
 */
(function () {
  'use strict';

  // En el modo de prueba (capturas sin interfaz) se usan temporizadores: requestAnimationFrame
  // no avanza con el tiempo virtual del navegador sin pantalla.
  const PRUEBA = /(^|[#&])prueba/.test(location.hash);
  const cuadro = PRUEBA ? (f) => setTimeout(() => f(performance.now()), 33) : (f) => requestAnimationFrame(f);

  const COLORES = ['#7cc4ff', '#f28b7f', '#7ee0b5', '#b39dff', '#ffb36b', '#ff8fd1', '#6fe3e3', '#d8e36f'];
  const ORO = '#ffd27a';
  const VERDE = '#7ee0b5';
  const SALMON = '#f28b7f';
  const TEXTO = '#eef1f8';
  const TENUE = '#9aa6c4';

  function bonito(v) {
    if (v === null || v === undefined || !isFinite(v)) return '';
    if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v));
    return (Math.round(v * 100) / 100).toString();
  }

  function pasoEje(lim) {
    const crudo = lim / 6;
    const p = Math.pow(10, Math.floor(Math.log10(crudo)));
    for (const k of [1, 2, 2.5, 5, 10]) if (crudo <= k * p) return k * p;
    return 10 * p;
  }

  function recortar(poly, a1, a2, b, signo) {
    // conserva los puntos con signo·(a1x + a2y − b) ≤ 0
    const dentro = (p) => signo * (a1 * p[0] + a2 * p[1] - b) <= 1e-9;
    const out = [];
    for (let i = 0; i < poly.length; i++) {
      const c = poly[i];
      const n = poly[(i + 1) % poly.length];
      const ci = dentro(c);
      const ni = dentro(n);
      if (ci) out.push(c);
      if (ci !== ni) {
        const f1 = signo * (a1 * c[0] + a2 * c[1] - b);
        const f2 = signo * (a1 * n[0] + a2 * n[1] - b);
        const t = f1 / (f1 - f2);
        out.push([c[0] + t * (n[0] - c[0]), c[1] + t * (n[1] - c[1])]);
      }
    }
    return out;
  }

  function semiplano(poly, r, b) {
    if (r.signo === '<=') return recortar(poly, r.a1, r.a2, b, 1);
    if (r.signo === '>=') return recortar(poly, r.a1, r.a2, b, -1);
    return recortar(recortar(poly, r.a1, r.a2, b, 1), r.a1, r.a2, b, -1);
  }

  const SUB = { 0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄', 5: '₅', 6: '₆', 7: '₇', 8: '₈', 9: '₉' };
  /** Fórmula para el lienzo (sin HTML): x1 → x₁ y "-" → "−". */
  function mate(t) {
    return String(t)
      .replace(/(?<![A-Za-z_])([xsea])(\d+)\b/g, (m, l, d) => l + [...d].map((c) => SUB[c]).join(''))
      .replace(/(^|[\s(=,:])-(?=[\d.a-zA-Z(])/g, '$1−')
      .replace(/ - /g, ' − ');
  }

  function caja(ctx, x, y, lineas, color, fondo = 'rgba(10,15,31,0.85)', tam = 13) {
    lineas = lineas.map(mate);
    ctx.font = `600 ${tam}px Segoe UI, system-ui, sans-serif`;
    const w = Math.max(...lineas.map((l) => ctx.measureText(l).width)) + 14;
    const h = lineas.length * (tam + 4) + 8;
    ctx.fillStyle = fondo;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, 7);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = color;
    lineas.forEach((l, i) => ctx.fillText(l, x + 7, y + 4 + (i + 1) * (tam + 4) - 4));
    return [w, h];
  }

  // ====================================================================== 2D

  class Vista2D {
    constructor() {
      this.g = null;
      this.reiniciar();
    }

    reiniciar() {
      this.estado = {
        ejes: 0,               // 0..1 aparición de ejes
        restr: 0,              // restricciones visibles (1.5 = una completa y la mitad de la segunda)
        semiplano: null,       // {i, alfa}: sombrea lo que cumple una restricción sola
        region: 0,             // alfa de la región factible
        vertices: 0,           // alfa de los vértices
        conZ: false,           // rotular el Z de cada vértice
        resaltar: -1,          // restricción resaltada
        punto: null,           // {x, y, alfa, factible, texto}
        rastro: [],            // [[x, y], ...]
        lineaZ: null,          // {z, alfa, texto}
        segmento: null,        // {a:[x,y], b:[x,y], alfa}
        rayo: null,            // {desde:[x,y], dir:[dx,dy], t}
        bCambio: null,         // {i, b}: lado derecho modificado (sensibilidad)
        textoCentro: null,     // {texto, color, alfa}
        pulsos: [],            // [{x, y, t0, color}]
        brilloVertice: null,   // [x, y]
      };
    }

    usar(g) {
      this.g = g;
      this.reiniciar();
    }

    b(i) {
      const e = this.estado;
      return e.bCambio && e.bCambio.i === i ? e.bCambio.b : this.g.rectas[i].b;
    }

    pintar(ctx, W, H) {
      const g = this.g;
      if (!g) return;
      const e = this.estado;
      const L = g.lim;
      const mi = 58, md = 26, ms = 70, mb = 50;
      const x0 = -0.06 * L;
      const sx = (W - mi - md) / (L - x0);
      const sy = (H - ms - mb) / (L - x0);
      const X = (x) => mi + (x - x0) * sx;
      const Y = (y) => H - mb - (y - x0) * sy;
      this.X = X;
      this.Y = Y;

      // cuadrícula y ejes
      const paso = pasoEje(L);
      ctx.globalAlpha = e.ejes;
      ctx.strokeStyle = 'rgba(154,166,196,0.10)';
      ctx.lineWidth = 1;
      ctx.fillStyle = TENUE;
      ctx.font = '12px Segoe UI, system-ui';
      for (let v = 0; v <= L + 1e-9; v += paso) {
        ctx.beginPath();
        ctx.moveTo(X(v), Y(x0));
        ctx.lineTo(X(v), Y(L));
        ctx.moveTo(X(x0), Y(v));
        ctx.lineTo(X(L), Y(v));
        ctx.stroke();
        ctx.textAlign = 'center';
        ctx.fillText(bonito(v), X(v), Y(0) + 18);
        ctx.textAlign = 'right';
        if (v > 0) ctx.fillText(bonito(v), X(0) - 8, Y(v) + 4);
      }
      ctx.strokeStyle = 'rgba(238,241,248,0.75)';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(X(x0), Y(0));
      ctx.lineTo(X(L), Y(0));
      ctx.moveTo(X(0), Y(x0));
      ctx.lineTo(X(0), Y(L));
      ctx.stroke();
      ctx.fillStyle = TEXTO;
      ctx.font = 'italic 600 15px Segoe UI, system-ui';
      ctx.textAlign = 'right';
      ctx.fillText('x₁', X(L) - 4, Y(0) - 8);
      ctx.textAlign = 'left';
      ctx.fillText('x₂', X(0) + 8, Y(L) + 14);
      ctx.globalAlpha = 1;

      const caja0 = [[0, 0], [L, 0], [L, L], [0, L]];
      const nVis = Math.floor(e.restr + 1e-9);

      // semiplano de una sola restricción
      if (e.semiplano && e.semiplano.alfa > 0) {
        const r = g.rectas[e.semiplano.i];
        const poly = semiplano(caja0, r, this.b(e.semiplano.i));
        if (poly.length >= 3) {
          ctx.globalAlpha = e.semiplano.alfa * 0.22;
          ctx.fillStyle = COLORES[e.semiplano.i % COLORES.length];
          this.poligono(ctx, poly);
          ctx.fill();
          ctx.globalAlpha = 1;
        }
      }

      // región factible
      if (e.region > 0) {
        let poly = caja0;
        for (let i = 0; i < Math.min(nVis, g.rectas.length); i++) {
          poly = semiplano(poly, g.rectas[i], this.b(i));
          if (!poly.length) break;
        }
        if (poly.length >= 3) {
          const grad = ctx.createLinearGradient(X(0), Y(0), X(L), Y(L));
          grad.addColorStop(0, 'rgba(124,196,255,0.42)');
          grad.addColorStop(1, 'rgba(179,157,255,0.30)');
          ctx.globalAlpha = e.region;
          ctx.fillStyle = grad;
          this.poligono(ctx, poly);
          ctx.fill();
          ctx.strokeStyle = 'rgba(124,196,255,0.9)';
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.globalAlpha = 1;
        } else if (poly.length === 2) {
          ctx.globalAlpha = e.region;
          ctx.strokeStyle = 'rgba(124,196,255,0.9)';
          ctx.lineWidth = 7;
          ctx.beginPath();
          ctx.moveTo(X(poly[0][0]), Y(poly[0][1]));
          ctx.lineTo(X(poly[1][0]), Y(poly[1][1]));
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }

      // restricciones (la última visible puede estar a medio dibujar)
      ctx.save();
      ctx.beginPath();
      ctx.rect(X(x0), Y(L), X(L) - X(x0), Y(x0) - Y(L));
      ctx.clip();
      const etiquetas = [];
      for (let i = 0; i < g.rectas.length; i++) {
        const prog = Math.max(0, Math.min(1, e.restr - i));
        if (prog <= 0) continue;
        const r = g.rectas[i];
        const b = this.b(i);
        const seg = this.segmentoRecta(r.a1, r.a2, b, x0, L);
        if (!seg) continue;
        const [p, q] = seg;
        const qx = p[0] + (q[0] - p[0]) * prog;
        const qy = p[1] + (q[1] - p[1]) * prog;
        const col = COLORES[i % COLORES.length];
        ctx.strokeStyle = col;
        ctx.lineWidth = e.resaltar === i ? 4.5 : 2.4;
        ctx.shadowColor = col;
        ctx.shadowBlur = e.resaltar === i ? 18 : 6;
        ctx.setLineDash(r.redundante && e.region > 0.5 ? [9, 7] : []);
        ctx.beginPath();
        ctx.moveTo(X(p[0]), Y(p[1]));
        ctx.lineTo(X(qx), Y(qy));
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
        if (prog >= 1) etiquetas.push({ i, r, p, q, col });
      }
      ctx.restore();

      // rótulos de las restricciones
      ctx.font = '600 13px Segoe UI, system-ui';
      for (const { i, r, p, q, col } of etiquetas) {
        // punto a 82 % del segmento visible, dentro de la vista
        const t = 0.8;
        let lx = X(p[0] + (q[0] - p[0]) * t);
        let ly = Y(p[1] + (q[1] - p[1]) * t);
        const texto = (e.bCambio && e.bCambio.i === i) ? r.txt.replace(/[-\d./]+$/, bonito(this.b(i))) : r.txt;
        const w = ctx.measureText(texto).width + 14;
        lx = Math.min(Math.max(lx - w / 2, X(x0) + 4), X(L) - w - 4);
        ly = Math.min(Math.max(ly - 30, Y(L) + 4), Y(x0) - 28);
        caja(ctx, lx, ly, [texto + (r.redundante && e.region > 0.5 ? '  (redundante)' : '')], col);
      }

      // recta de Z
      if (e.lineaZ && e.lineaZ.alfa > 0 && g.c) {
        const seg = this.segmentoRecta(g.c[0], g.c[1], e.lineaZ.z, x0, L);
        if (seg) {
          ctx.save();
          ctx.globalAlpha = e.lineaZ.alfa;
          ctx.strokeStyle = ORO;
          ctx.lineWidth = 2.6;
          ctx.setLineDash([12, 8]);
          ctx.shadowColor = ORO;
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.moveTo(X(seg[0][0]), Y(seg[0][1]));
          ctx.lineTo(X(seg[1][0]), Y(seg[1][1]));
          ctx.stroke();
          ctx.restore();
          if (e.lineaZ.texto) {
            const m = [(seg[0][0] * 0.15 + seg[1][0] * 0.85), (seg[0][1] * 0.15 + seg[1][1] * 0.85)];
            ctx.globalAlpha = e.lineaZ.alfa;
            caja(ctx, Math.min(X(m[0]) + 8, X(L) - 120), Math.max(Y(m[1]) - 36, Y(L) + 4), [e.lineaZ.texto], ORO);
            ctx.globalAlpha = 1;
          }
        }
      }

      // segmento de óptimos múltiples
      if (e.segmento && e.segmento.alfa > 0) {
        ctx.save();
        ctx.globalAlpha = e.segmento.alfa;
        ctx.strokeStyle = ORO;
        ctx.lineWidth = 9;
        ctx.lineCap = 'round';
        ctx.shadowColor = ORO;
        ctx.shadowBlur = 26;
        ctx.beginPath();
        ctx.moveTo(X(e.segmento.a[0]), Y(e.segmento.a[1]));
        ctx.lineTo(X(e.segmento.b[0]), Y(e.segmento.b[1]));
        ctx.stroke();
        ctx.restore();
      }

      // vértices
      if (e.vertices > 0) {
        ctx.globalAlpha = e.vertices;
        for (const v of g.vertices) {
          const brilla = e.brilloVertice && Math.abs(e.brilloVertice[0] - v.x) < 1e-9 && Math.abs(e.brilloVertice[1] - v.y) < 1e-9;
          ctx.fillStyle = brilla ? ORO : TEXTO;
          ctx.beginPath();
          ctx.arc(X(v.x), Y(v.y), brilla ? 7 : 5, 0, Math.PI * 2);
          ctx.fill();
          if (e.conZ) {
            const lin = [`(${v.xs}, ${v.ys})`, `Z = ${v.zs}`];
            const dx = X(v.x) > X(L) * 0.75 ? -118 : 10;
            caja(ctx, X(v.x) + dx, Y(v.y) - 46, lin, brilla ? ORO : TENUE, 'rgba(10,15,31,0.85)', 12);
          }
        }
        ctx.globalAlpha = 1;
      }

      // rastro del simplex
      if (e.rastro.length > 1) {
        ctx.save();
        ctx.strokeStyle = ORO;
        ctx.lineWidth = 3.5;
        ctx.shadowColor = ORO;
        ctx.shadowBlur = 14;
        ctx.beginPath();
        e.rastro.forEach((p, k) => (k ? ctx.lineTo(X(p[0]), Y(p[1])) : ctx.moveTo(X(p[0]), Y(p[1]))));
        ctx.stroke();
        ctx.restore();
      }

      // rayo al infinito
      if (e.rayo && e.rayo.t > 0) {
        const [px, py] = e.rayo.desde;
        const [dx, dy] = e.rayo.dir;
        const n = Math.hypot(dx, dy) || 1;
        const len = L * 1.6 * e.rayo.t;
        const qx = px + (dx / n) * len;
        const qy = py + (dy / n) * len;
        ctx.save();
        ctx.beginPath();
        ctx.rect(X(x0), Y(L), X(L) - X(x0), Y(x0) - Y(L));
        ctx.clip();
        ctx.strokeStyle = SALMON;
        ctx.lineWidth = 4;
        ctx.shadowColor = SALMON;
        ctx.shadowBlur = 18;
        ctx.beginPath();
        ctx.moveTo(X(px), Y(py));
        ctx.lineTo(X(qx), Y(qy));
        ctx.stroke();
        ctx.restore();
        if (e.rayo.t > 0.6) {
          ctx.fillStyle = SALMON;
          ctx.font = '700 34px Segoe UI, system-ui';
          ctx.textAlign = 'right';
          ctx.fillText('→ ∞', X(L) - 14, Y(L) + 44);
          ctx.textAlign = 'left';
        }
      }

      // pulsos (destellos en un punto)
      const ahora = performance.now();
      e.pulsos = e.pulsos.filter((p) => ahora - p.t0 < 1200);
      for (const p of e.pulsos) {
        const k = (ahora - p.t0) / 1200;
        ctx.strokeStyle = p.color || ORO;
        ctx.globalAlpha = 1 - k;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(X(p.x), Y(p.y), 8 + k * 46, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // punto actual del simplex
      if (e.punto && e.punto.alfa > 0) {
        const { x, y, factible, texto } = e.punto;
        const col = factible === false ? SALMON : VERDE;
        ctx.globalAlpha = e.punto.alfa;
        const r0 = 9 + 2 * Math.sin(ahora / 260);
        const grad = ctx.createRadialGradient(X(x), Y(y), 0, X(x), Y(y), 34);
        grad.addColorStop(0, col);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(X(x), Y(y), 34, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(X(x), Y(y), r0 * 0.55, 0, Math.PI * 2);
        ctx.fill();
        if (texto) {
          const dx = X(x) > X(L) * 0.7 ? -150 : 18;
          caja(ctx, X(x) + dx, Y(y) + 14, texto.split('\n'), col, 'rgba(10,15,31,0.9)', 14);
        }
        ctx.globalAlpha = 1;
      }

      // texto grande al centro
      if (e.textoCentro && e.textoCentro.alfa > 0) {
        ctx.globalAlpha = e.textoCentro.alfa;
        ctx.font = '800 44px Segoe UI, system-ui';
        ctx.textAlign = 'center';
        ctx.fillStyle = e.textoCentro.color || SALMON;
        ctx.shadowColor = e.textoCentro.color || SALMON;
        ctx.shadowBlur = 24;
        ctx.fillText(e.textoCentro.texto, W / 2, H / 2);
        ctx.shadowBlur = 0;
        ctx.textAlign = 'left';
        ctx.globalAlpha = 1;
      }
    }

    poligono(ctx, poly) {
      ctx.beginPath();
      poly.forEach((p, k) => (k ? ctx.lineTo(this.X(p[0]), this.Y(p[1])) : ctx.moveTo(this.X(p[0]), this.Y(p[1]))));
      ctx.closePath();
    }

    /** Extremos de la recta a1·x + a2·y = b dentro de la ventana [x0, L]². */
    segmentoRecta(a1, a2, b, x0, L) {
      const pts = [];
      const add = (x, y) => {
        if (x >= x0 - 1e-9 && x <= L + 1e-9 && y >= x0 - 1e-9 && y <= L + 1e-9) pts.push([x, y]);
      };
      if (Math.abs(a2) > 1e-12) {
        add(x0, (b - a1 * x0) / a2);
        add(L, (b - a1 * L) / a2);
      }
      if (Math.abs(a1) > 1e-12) {
        add((b - a2 * x0) / a1, x0);
        add((b - a2 * L) / a1, L);
      }
      if (pts.length < 2) return null;
      pts.sort((u, v) => u[0] - v[0] || u[1] - v[1]);
      return [pts[0], pts[pts.length - 1]];
    }
  }

  // ====================================================================== 3D

  class Vista3D {
    constructor() {
      this.p = null;
      this.ang = -0.9;
      this.inc = 0.42;
      this.auto = true;
      this.reiniciar();
    }

    reiniciar() {
      this.estado = { ejes: 0, caras: 0, aristas: 0, vertices: 0, punto: null, rastro: [], resaltarCara: -1, carasVisibles: 99,
        textoCentro: null, conZ: false };
    }

    usar(p) {
      this.p = p;
      // escala propia por eje para que el poliedro se vea completo aunque los rangos sean distintos
      this.lims = p && !p.vacia ? [0, 1, 2].map((k) => Math.max(...p.vertices.map((v) => v.p[k])) || p.lim) : [1, 1, 1];
      this.reiniciar();
    }

    proyectar(v, W, H) {
      const [lx, ly, lz] = this.lims;
      // coordenadas: x1 → x, x2 → y, x3 → arriba
      const x = v[0] / lx - 0.45, y = v[1] / ly - 0.45, z = v[2] / lz - 0.45;
      const ca = Math.cos(this.ang), sa = Math.sin(this.ang);
      const xr = x * ca - y * sa;
      const yr = x * sa + y * ca;
      const ci = Math.cos(this.inc), si = Math.sin(this.inc);
      const yv = yr * ci + z * si;    // profundidad
      const zv = -yr * si + z * ci;   // altura en pantalla
      const esc = Math.min(W, H) * 0.5;
      const persp = 1 / (1 + yv * 0.35);
      return [W / 2 + xr * esc * persp, H * 0.56 - zv * esc * persp, yv];
    }

    pintar(ctx, W, H, dt) {
      const P = this.p;
      if (!P || P.vacia) return;
      const e = this.estado;
      if (this.auto) this.ang += dt * 0.00018;
      const pr = (v) => this.proyectar(v, W, H);
      const L = P.lim;

      // ejes
      ctx.globalAlpha = e.ejes;
      const nombres = ['x₁', 'x₂', 'x₃'];
      for (let k = 0; k < 3; k++) {
        const fin = [0, 0, 0];
        fin[k] = this.lims[k] * 1.3;
        const a = pr([0, 0, 0]);
        const b = pr(fin);
        ctx.strokeStyle = 'rgba(238,241,248,0.7)';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(a[0], a[1]);
        ctx.lineTo(b[0], b[1]);
        ctx.stroke();
        ctx.fillStyle = TEXTO;
        ctx.font = 'italic 600 16px Segoe UI';
        ctx.fillText(mate(nombres[k]), b[0] + 6, b[1]);
      }
      ctx.globalAlpha = 1;

      const V = P.vertices.map((v) => pr(v.p));
      // caras ordenadas de atrás hacia adelante
      if (e.caras > 0) {
        const caras = P.caras.map((c, k) => ({ c, k, d: c.v.reduce((s, i) => s + V[i][2], 0) / c.v.length }))
          .filter(({ c }) => c.r < e.carasVisibles)
          .sort((a, b) => b.d - a.d);
        for (const { c } of caras) {
          const col = c.tipo === 'r' ? COLORES[c.r % COLORES.length] : '#7c8bb5';
          ctx.globalAlpha = e.caras * (c.tipo === 'r' ? (e.resaltarCara === c.r ? 0.55 : 0.22) : 0.1);
          ctx.fillStyle = col;
          ctx.beginPath();
          c.v.forEach((i, k) => (k ? ctx.lineTo(V[i][0], V[i][1]) : ctx.moveTo(V[i][0], V[i][1])));
          ctx.closePath();
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      }
      if (e.aristas > 0) {
        ctx.globalAlpha = e.aristas;
        ctx.strokeStyle = 'rgba(124,196,255,0.85)';
        ctx.lineWidth = 1.6;
        for (const [i, j] of P.aristas) {
          ctx.beginPath();
          ctx.moveTo(V[i][0], V[i][1]);
          ctx.lineTo(V[j][0], V[j][1]);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
      if (e.vertices > 0) {
        ctx.globalAlpha = e.vertices;
        P.vertices.forEach((v, k) => {
          ctx.fillStyle = TEXTO;
          ctx.beginPath();
          ctx.arc(V[k][0], V[k][1], 4, 0, Math.PI * 2);
          ctx.fill();
          if (e.conZ) {
            ctx.font = '11px Segoe UI';
            ctx.fillStyle = TENUE;
            ctx.fillText(mate(`(${v.s.join(', ')}) Z = ${v.z}`), V[k][0] + 6, V[k][1] - 6);
          }
        });
        ctx.globalAlpha = 1;
      }
      if (e.rastro.length > 1) {
        ctx.save();
        ctx.strokeStyle = ORO;
        ctx.lineWidth = 4;
        ctx.shadowColor = ORO;
        ctx.shadowBlur = 16;
        ctx.beginPath();
        e.rastro.forEach((p, k) => {
          const q = pr(p);
          k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]);
        });
        ctx.stroke();
        ctx.restore();
      }
      if (e.punto && e.punto.alfa > 0) {
        const q = pr(e.punto.p);
        const col = e.punto.factible === false ? SALMON : VERDE;
        ctx.globalAlpha = e.punto.alfa;
        const grad = ctx.createRadialGradient(q[0], q[1], 0, q[0], q[1], 30);
        grad.addColorStop(0, col);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(q[0], q[1], 30, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(q[0], q[1], 5, 0, Math.PI * 2);
        ctx.fill();
        if (e.punto.texto) caja(ctx, q[0] + 16, q[1] + 10, e.punto.texto.split('\n'), col, 'rgba(10,15,31,0.9)', 14);
        ctx.globalAlpha = 1;
      }
      if (!P.acotada && e.caras > 0) {
        ctx.fillStyle = TENUE;
        ctx.font = '13px Segoe UI';
        ctx.fillText('Región no acotada (recortada para dibujarla)', 16, H - 16);
      }
    }
  }

  // ====================================================================== lienzo

  class Lienzo {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.v2 = new Vista2D();
      this.v3 = new Vista3D();
      this.modo = 'nada'; // '2d' | '3d' | 'nada'
      this.ultimo = performance.now();
      this.arrastre = null;
      canvas.addEventListener('pointerdown', (ev) => {
        if (this.modo !== '3d') return;
        this.arrastre = [ev.clientX, ev.clientY, this.v3.ang, this.v3.inc];
        this.v3.auto = false;
        canvas.setPointerCapture(ev.pointerId);
      });
      canvas.addEventListener('pointermove', (ev) => {
        if (!this.arrastre) return;
        const [x, y, a, i] = this.arrastre;
        this.v3.ang = a + (ev.clientX - x) * 0.008;
        this.v3.inc = Math.max(-0.2, Math.min(1.35, i + (ev.clientY - y) * 0.006));
      });
      canvas.addEventListener('pointerup', () => (this.arrastre = null));
      canvas.addEventListener('dblclick', () => (this.v3.auto = true));
      const bucle = (t) => {
        this.pintar(t - this.ultimo);
        this.ultimo = t;
        cuadro(bucle);
      };
      cuadro(bucle);
    }

    pintar(dt) {
      const c = this.canvas;
      const dpr = window.devicePixelRatio || 1;
      const W = c.clientWidth, H = c.clientHeight;
      if (!W || !H) return;
      if (c.width !== Math.round(W * dpr) || c.height !== Math.round(H * dpr)) {
        c.width = Math.round(W * dpr);
        c.height = Math.round(H * dpr);
      }
      const ctx = this.ctx;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      if (this.modo === '2d') this.v2.pintar(ctx, W, H);
      else if (this.modo === '3d') this.v3.pintar(ctx, W, H, Math.min(dt, 50));
    }
  }

  window.Dibujo = { Lienzo, COLORES, bonito, cuadro, mate };
})();
