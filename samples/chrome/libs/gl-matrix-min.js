/*
 * RedGL - MIT License
 * Copyright (c) 2018 - 2019 By RedCamel(webseon@gmail.com)
 * https://github.com/redcamel/RedGL2/blob/dev/LICENSE
 * Last modification time of this file - 2019.5.8 11:23
 */
!function (t, n) {
	"object" == typeof exports && "undefined" != typeof module ? n(exports) : "function" == typeof define && define.amd ? define(["exports"], n) : n(t.glMatrix = {})
}(this, function (t) {
	"use strict";
	var n = 1e-6, a = "undefined" != typeof Float32Array ? Float32Array : Array, r = Math.random;
	var u = Math.PI / 180;
	var e = Object.freeze({
		EPSILON: n, get ARRAY_TYPE() {
			return a
		}, RANDOM: r, setMatrixArrayType: function (t) {
			a = t
		}, toRadian: function (t) {
			return t * u
		}, equals: function (t, a) {
			return Math.abs(t - a) <= n * Math.max(1, Math.abs(t), Math.abs(a))
		}
	});

	function o(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = a[0], h = a[1], c = a[2], M = a[3];
		return t[0] = r * i + e * h, t[1] = u * i + o * h, t[2] = r * c + e * M, t[3] = u * c + o * M, t
	}

	function i(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t[3] = n[3] - a[3], t
	}

	var h = o, c = i, M = Object.freeze({
		create: function () {
			var t = new a(4);
			return a != Float32Array && (t[1] = 0, t[2] = 0), t[0] = 1, t[3] = 1, t
		}, clone: function (t) {
			var n = new a(4);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n
		}, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t
		}, identity: function (t) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 1, t
		}, fromValues: function (t, n, r, u) {
			var e = new a(4);
			return e[0] = t, e[1] = n, e[2] = r, e[3] = u, e
		}, set: function (t, n, a, r, u) {
			return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t
		}, transpose: function (t, n) {
			if (t === n) {
				var a = n[1];
				t[1] = n[2], t[2] = a
			} else t[0] = n[0], t[1] = n[2], t[2] = n[1], t[3] = n[3];
			return t
		}, invert: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = a * e - u * r;
			return o ? (o = 1 / o, t[0] = e * o, t[1] = -r * o, t[2] = -u * o, t[3] = a * o, t) : null
		}, adjoint: function (t, n) {
			var a = n[0];
			return t[0] = n[3], t[1] = -n[1], t[2] = -n[2], t[3] = a, t
		}, determinant: function (t) {
			return t[0] * t[3] - t[2] * t[1]
		}, multiply: o, rotate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = Math.sin(a), h = Math.cos(a);
			return t[0] = r * h + e * i, t[1] = u * h + o * i, t[2] = r * -i + e * h, t[3] = u * -i + o * h, t
		}, scale: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = a[0], h = a[1];
			return t[0] = r * i, t[1] = u * i, t[2] = e * h, t[3] = o * h, t
		}, fromRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = r, t[1] = a, t[2] = -a, t[3] = r, t
		}, fromScaling: function (t, n) {
			return t[0] = n[0], t[1] = 0, t[2] = 0, t[3] = n[1], t
		}, str: function (t) {
			return "mat2(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ")"
		}, frob: function (t) {
			return Math.sqrt(Math.pow(t[0], 2) + Math.pow(t[1], 2) + Math.pow(t[2], 2) + Math.pow(t[3], 2))
		}, LDU: function (t, n, a, r) {
			return t[2] = r[2] / r[0], a[0] = r[0], a[1] = r[1], a[3] = r[3] - t[2] * a[1], [t, n, a]
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t
		}, subtract: i, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = t[3], i = a[0], h = a[1], c = a[2], M = a[3];
			return Math.abs(r - i) <= n * Math.max(1, Math.abs(r), Math.abs(i)) && Math.abs(u - h) <= n * Math.max(1, Math.abs(u), Math.abs(h)) && Math.abs(e - c) <= n * Math.max(1, Math.abs(e), Math.abs(c)) && Math.abs(o - M) <= n * Math.max(1, Math.abs(o), Math.abs(M))
		}, multiplyScalar: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t
		}, multiplyScalarAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t[3] = n[3] + a[3] * r, t
		}, mul: h, sub: c
	});

	function s(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = a[0], M = a[1], s = a[2], f = a[3],
			l = a[4], v = a[5];
		return t[0] = r * c + e * M, t[1] = u * c + o * M, t[2] = r * s + e * f, t[3] = u * s + o * f, t[4] = r * l + e * v + i, t[5] = u * l + o * v + h, t
	}

	function f(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t[3] = n[3] - a[3], t[4] = n[4] - a[4], t[5] = n[5] - a[5], t
	}

	var l = s, v = f, b = Object.freeze({
		create: function () {
			var t = new a(6);
			return a != Float32Array && (t[1] = 0, t[2] = 0, t[4] = 0, t[5] = 0), t[0] = 1, t[3] = 1, t
		}, clone: function (t) {
			var n = new a(6);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n[4] = t[4], n[5] = t[5], n
		}, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t
		}, identity: function (t) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 1, t[4] = 0, t[5] = 0, t
		}, fromValues: function (t, n, r, u, e, o) {
			var i = new a(6);
			return i[0] = t, i[1] = n, i[2] = r, i[3] = u, i[4] = e, i[5] = o, i
		}, set: function (t, n, a, r, u, e, o) {
			return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t[4] = e, t[5] = o, t
		}, invert: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = a * e - r * u;
			return h ? (h = 1 / h, t[0] = e * h, t[1] = -r * h, t[2] = -u * h, t[3] = a * h, t[4] = (u * i - e * o) * h, t[5] = (r * o - a * i) * h, t) : null
		}, determinant: function (t) {
			return t[0] * t[3] - t[1] * t[2]
		}, multiply: s, rotate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = Math.sin(a), M = Math.cos(a);
			return t[0] = r * M + e * c, t[1] = u * M + o * c, t[2] = r * -c + e * M, t[3] = u * -c + o * M, t[4] = i, t[5] = h, t
		}, scale: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = a[0], M = a[1];
			return t[0] = r * c, t[1] = u * c, t[2] = e * M, t[3] = o * M, t[4] = i, t[5] = h, t
		}, translate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = a[0], M = a[1];
			return t[0] = r, t[1] = u, t[2] = e, t[3] = o, t[4] = r * c + e * M + i, t[5] = u * c + o * M + h, t
		}, fromRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = r, t[1] = a, t[2] = -a, t[3] = r, t[4] = 0, t[5] = 0, t
		}, fromScaling: function (t, n) {
			return t[0] = n[0], t[1] = 0, t[2] = 0, t[3] = n[1], t[4] = 0, t[5] = 0, t
		}, fromTranslation: function (t, n) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 1, t[4] = n[0], t[5] = n[1], t
		}, str: function (t) {
			return "mat2d(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ", " + t[4] + ", " + t[5] + ")"
		}, frob: function (t) {
			return Math.sqrt(Math.pow(t[0], 2) + Math.pow(t[1], 2) + Math.pow(t[2], 2) + Math.pow(t[3], 2) + Math.pow(t[4], 2) + Math.pow(t[5], 2) + 1)
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t[4] = n[4] + a[4], t[5] = n[5] + a[5], t
		}, subtract: f, multiplyScalar: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t[4] = n[4] * a, t[5] = n[5] * a, t
		}, multiplyScalarAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t[3] = n[3] + a[3] * r, t[4] = n[4] + a[4] * r, t[5] = n[5] + a[5] * r, t
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3] && t[4] === n[4] && t[5] === n[5]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = t[3], i = t[4], h = t[5], c = a[0], M = a[1], s = a[2], f = a[3],
				l = a[4], v = a[5];
			return Math.abs(r - c) <= n * Math.max(1, Math.abs(r), Math.abs(c)) && Math.abs(u - M) <= n * Math.max(1, Math.abs(u), Math.abs(M)) && Math.abs(e - s) <= n * Math.max(1, Math.abs(e), Math.abs(s)) && Math.abs(o - f) <= n * Math.max(1, Math.abs(o), Math.abs(f)) && Math.abs(i - l) <= n * Math.max(1, Math.abs(i), Math.abs(l)) && Math.abs(h - v) <= n * Math.max(1, Math.abs(h), Math.abs(v))
		}, mul: l, sub: v
	});

	function m() {
		var t = new a(9);
		return a != Float32Array && (t[1] = 0, t[2] = 0, t[3] = 0, t[5] = 0, t[6] = 0, t[7] = 0), t[0] = 1, t[4] = 1, t[8] = 1, t
	}

	function d(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7], s = n[8], f = a[0],
			l = a[1], v = a[2], b = a[3], m = a[4], d = a[5], p = a[6], x = a[7], q = a[8];
		return t[0] = f * r + l * o + v * c, t[1] = f * u + l * i + v * M, t[2] = f * e + l * h + v * s, t[3] = b * r + m * o + d * c, t[4] = b * u + m * i + d * M, t[5] = b * e + m * h + d * s, t[6] = p * r + x * o + q * c, t[7] = p * u + x * i + q * M, t[8] = p * e + x * h + q * s, t
	}

	function p(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t[3] = n[3] - a[3], t[4] = n[4] - a[4], t[5] = n[5] - a[5], t[6] = n[6] - a[6], t[7] = n[7] - a[7], t[8] = n[8] - a[8], t
	}

	var x = d, q = p, w = Object.freeze({
		create: m, fromMat4: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[4], t[4] = n[5], t[5] = n[6], t[6] = n[8], t[7] = n[9], t[8] = n[10], t
		}, clone: function (t) {
			var n = new a(9);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n[4] = t[4], n[5] = t[5], n[6] = t[6], n[7] = t[7], n[8] = t[8], n
		}, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t[8] = n[8], t
		}, fromValues: function (t, n, r, u, e, o, i, h, c) {
			var M = new a(9);
			return M[0] = t, M[1] = n, M[2] = r, M[3] = u, M[4] = e, M[5] = o, M[6] = i, M[7] = h, M[8] = c, M
		}, set: function (t, n, a, r, u, e, o, i, h, c) {
			return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t[4] = e, t[5] = o, t[6] = i, t[7] = h, t[8] = c, t
		}, identity: function (t) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 1, t[5] = 0, t[6] = 0, t[7] = 0, t[8] = 1, t
		}, transpose: function (t, n) {
			if (t === n) {
				var a = n[1], r = n[2], u = n[5];
				t[1] = n[3], t[2] = n[6], t[3] = a, t[5] = n[7], t[6] = r, t[7] = u
			} else t[0] = n[0], t[1] = n[3], t[2] = n[6], t[3] = n[1], t[4] = n[4], t[5] = n[7], t[6] = n[2], t[7] = n[5], t[8] = n[8];
			return t
		}, invert: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = n[6], c = n[7], M = n[8],
				s = M * o - i * c, f = -M * e + i * h, l = c * e - o * h, v = a * s + r * f + u * l;
			return v ? (v = 1 / v, t[0] = s * v, t[1] = (-M * r + u * c) * v, t[2] = (i * r - u * o) * v, t[3] = f * v, t[4] = (M * a - u * h) * v, t[5] = (-i * a + u * e) * v, t[6] = l * v, t[7] = (-c * a + r * h) * v, t[8] = (o * a - r * e) * v, t) : null
		}, adjoint: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = n[6], c = n[7], M = n[8];
			return t[0] = o * M - i * c, t[1] = u * c - r * M, t[2] = r * i - u * o, t[3] = i * h - e * M, t[4] = a * M - u * h, t[5] = u * e - a * i, t[6] = e * c - o * h, t[7] = r * h - a * c, t[8] = a * o - r * e, t
		}, determinant: function (t) {
			var n = t[0], a = t[1], r = t[2], u = t[3], e = t[4], o = t[5], i = t[6], h = t[7], c = t[8];
			return n * (c * e - o * h) + a * (-c * u + o * i) + r * (h * u - e * i)
		}, multiply: d, translate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7], s = n[8], f = a[0],
				l = a[1];
			return t[0] = r, t[1] = u, t[2] = e, t[3] = o, t[4] = i, t[5] = h, t[6] = f * r + l * o + c, t[7] = f * u + l * i + M, t[8] = f * e + l * h + s, t
		}, rotate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7], s = n[8],
				f = Math.sin(a), l = Math.cos(a);
			return t[0] = l * r + f * o, t[1] = l * u + f * i, t[2] = l * e + f * h, t[3] = l * o - f * r, t[4] = l * i - f * u, t[5] = l * h - f * e, t[6] = c, t[7] = M, t[8] = s, t
		}, scale: function (t, n, a) {
			var r = a[0], u = a[1];
			return t[0] = r * n[0], t[1] = r * n[1], t[2] = r * n[2], t[3] = u * n[3], t[4] = u * n[4], t[5] = u * n[5], t[6] = n[6], t[7] = n[7], t[8] = n[8], t
		}, fromTranslation: function (t, n) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 1, t[5] = 0, t[6] = n[0], t[7] = n[1], t[8] = 1, t
		}, fromRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = r, t[1] = a, t[2] = 0, t[3] = -a, t[4] = r, t[5] = 0, t[6] = 0, t[7] = 0, t[8] = 1, t
		}, fromScaling: function (t, n) {
			return t[0] = n[0], t[1] = 0, t[2] = 0, t[3] = 0, t[4] = n[1], t[5] = 0, t[6] = 0, t[7] = 0, t[8] = 1, t
		}, fromMat2d: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = 0, t[3] = n[2], t[4] = n[3], t[5] = 0, t[6] = n[4], t[7] = n[5], t[8] = 1, t
		}, fromQuat: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = a + a, i = r + r, h = u + u, c = a * o, M = r * o,
				s = r * i, f = u * o, l = u * i, v = u * h, b = e * o, m = e * i, d = e * h;
			return t[0] = 1 - s - v, t[3] = M - d, t[6] = f + m, t[1] = M + d, t[4] = 1 - c - v, t[7] = l - b, t[2] = f - m, t[5] = l + b, t[8] = 1 - c - s, t
		}, normalFromMat4: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = n[6], c = n[7], M = n[8], s = n[9],
				f = n[10], l = n[11], v = n[12], b = n[13], m = n[14], d = n[15], p = a * i - r * o, x = a * h - u * o,
				q = a * c - e * o, w = r * h - u * i, y = r * c - e * i, g = u * c - e * h, A = M * b - s * v,
				R = M * m - f * v, z = M * d - l * v, P = s * m - f * b, j = s * d - l * b, I = f * d - l * m,
				S = p * I - x * j + q * P + w * z - y * R + g * A;
			return S ? (S = 1 / S, t[0] = (i * I - h * j + c * P) * S, t[1] = (h * z - o * I - c * R) * S, t[2] = (o * j - i * z + c * A) * S, t[3] = (u * j - r * I - e * P) * S, t[4] = (a * I - u * z + e * R) * S, t[5] = (r * z - a * j - e * A) * S, t[6] = (b * g - m * y + d * w) * S, t[7] = (m * q - v * g - d * x) * S, t[8] = (v * y - b * q + d * p) * S, t) : null
		}, projection: function (t, n, a) {
			return t[0] = 2 / n, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = -2 / a, t[5] = 0, t[6] = -1, t[7] = 1, t[8] = 1, t
		}, str: function (t) {
			return "mat3(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ", " + t[4] + ", " + t[5] + ", " + t[6] + ", " + t[7] + ", " + t[8] + ")"
		}, frob: function (t) {
			return Math.sqrt(Math.pow(t[0], 2) + Math.pow(t[1], 2) + Math.pow(t[2], 2) + Math.pow(t[3], 2) + Math.pow(t[4], 2) + Math.pow(t[5], 2) + Math.pow(t[6], 2) + Math.pow(t[7], 2) + Math.pow(t[8], 2))
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t[4] = n[4] + a[4], t[5] = n[5] + a[5], t[6] = n[6] + a[6], t[7] = n[7] + a[7], t[8] = n[8] + a[8], t
		}, subtract: p, multiplyScalar: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t[4] = n[4] * a, t[5] = n[5] * a, t[6] = n[6] * a, t[7] = n[7] * a, t[8] = n[8] * a, t
		}, multiplyScalarAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t[3] = n[3] + a[3] * r, t[4] = n[4] + a[4] * r, t[5] = n[5] + a[5] * r, t[6] = n[6] + a[6] * r, t[7] = n[7] + a[7] * r, t[8] = n[8] + a[8] * r, t
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3] && t[4] === n[4] && t[5] === n[5] && t[6] === n[6] && t[7] === n[7] && t[8] === n[8]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = t[3], i = t[4], h = t[5], c = t[6], M = t[7], s = t[8], f = a[0],
				l = a[1], v = a[2], b = a[3], m = a[4], d = a[5], p = a[6], x = a[7], q = a[8];
			return Math.abs(r - f) <= n * Math.max(1, Math.abs(r), Math.abs(f)) && Math.abs(u - l) <= n * Math.max(1, Math.abs(u), Math.abs(l)) && Math.abs(e - v) <= n * Math.max(1, Math.abs(e), Math.abs(v)) && Math.abs(o - b) <= n * Math.max(1, Math.abs(o), Math.abs(b)) && Math.abs(i - m) <= n * Math.max(1, Math.abs(i), Math.abs(m)) && Math.abs(h - d) <= n * Math.max(1, Math.abs(h), Math.abs(d)) && Math.abs(c - p) <= n * Math.max(1, Math.abs(c), Math.abs(p)) && Math.abs(M - x) <= n * Math.max(1, Math.abs(M), Math.abs(x)) && Math.abs(s - q) <= n * Math.max(1, Math.abs(s), Math.abs(q))
		}, mul: x, sub: q
	});

	function y(t) {
		return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = 1, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[10] = 1, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
	}

	function g(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7], s = n[8], f = n[9],
			l = n[10], v = n[11], b = n[12], m = n[13], d = n[14], p = n[15], x = a[0], q = a[1], w = a[2], y = a[3];
		return t[0] = x * r + q * i + w * s + y * b, t[1] = x * u + q * h + w * f + y * m, t[2] = x * e + q * c + w * l + y * d, t[3] = x * o + q * M + w * v + y * p, x = a[4], q = a[5], w = a[6], y = a[7], t[4] = x * r + q * i + w * s + y * b, t[5] = x * u + q * h + w * f + y * m, t[6] = x * e + q * c + w * l + y * d, t[7] = x * o + q * M + w * v + y * p, x = a[8], q = a[9], w = a[10], y = a[11], t[8] = x * r + q * i + w * s + y * b, t[9] = x * u + q * h + w * f + y * m, t[10] = x * e + q * c + w * l + y * d, t[11] = x * o + q * M + w * v + y * p, x = a[12], q = a[13], w = a[14], y = a[15], t[12] = x * r + q * i + w * s + y * b, t[13] = x * u + q * h + w * f + y * m, t[14] = x * e + q * c + w * l + y * d, t[15] = x * o + q * M + w * v + y * p, t
	}

	function A(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = r + r, h = u + u, c = e + e, M = r * i, s = r * h, f = r * c,
			l = u * h, v = u * c, b = e * c, m = o * i, d = o * h, p = o * c;
		return t[0] = 1 - (l + b), t[1] = s + p, t[2] = f - d, t[3] = 0, t[4] = s - p, t[5] = 1 - (M + b), t[6] = v + m, t[7] = 0, t[8] = f + d, t[9] = v - m, t[10] = 1 - (M + l), t[11] = 0, t[12] = a[0], t[13] = a[1], t[14] = a[2], t[15] = 1, t
	}

	function R(t, n) {
		return t[0] = n[12], t[1] = n[13], t[2] = n[14], t
	}

	function z(t, n) {
		var a = n[0] + n[5] + n[10], r = 0;
		return a > 0 ? (r = 2 * Math.sqrt(a + 1), t[3] = .25 * r, t[0] = (n[6] - n[9]) / r, t[1] = (n[8] - n[2]) / r, t[2] = (n[1] - n[4]) / r) : n[0] > n[5] && n[0] > n[10] ? (r = 2 * Math.sqrt(1 + n[0] - n[5] - n[10]), t[3] = (n[6] - n[9]) / r, t[0] = .25 * r, t[1] = (n[1] + n[4]) / r, t[2] = (n[8] + n[2]) / r) : n[5] > n[10] ? (r = 2 * Math.sqrt(1 + n[5] - n[0] - n[10]), t[3] = (n[8] - n[2]) / r, t[0] = (n[1] + n[4]) / r, t[1] = .25 * r, t[2] = (n[6] + n[9]) / r) : (r = 2 * Math.sqrt(1 + n[10] - n[0] - n[5]), t[3] = (n[1] - n[4]) / r, t[0] = (n[8] + n[2]) / r, t[1] = (n[6] + n[9]) / r, t[2] = .25 * r), t
	}

	function P(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t[3] = n[3] - a[3], t[4] = n[4] - a[4], t[5] = n[5] - a[5], t[6] = n[6] - a[6], t[7] = n[7] - a[7], t[8] = n[8] - a[8], t[9] = n[9] - a[9], t[10] = n[10] - a[10], t[11] = n[11] - a[11], t[12] = n[12] - a[12], t[13] = n[13] - a[13], t[14] = n[14] - a[14], t[15] = n[15] - a[15], t
	}

	var j = g, I = P, S = Object.freeze({
		create: function () {
			var t = new a(16);
			return a != Float32Array && (t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0), t[0] = 1, t[5] = 1, t[10] = 1, t[15] = 1, t
		}, clone: function (t) {
			var n = new a(16);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n[4] = t[4], n[5] = t[5], n[6] = t[6], n[7] = t[7], n[8] = t[8], n[9] = t[9], n[10] = t[10], n[11] = t[11], n[12] = t[12], n[13] = t[13], n[14] = t[14], n[15] = t[15], n
		}, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t[8] = n[8], t[9] = n[9], t[10] = n[10], t[11] = n[11], t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15], t
		}, fromValues: function (t, n, r, u, e, o, i, h, c, M, s, f, l, v, b, m) {
			var d = new a(16);
			return d[0] = t, d[1] = n, d[2] = r, d[3] = u, d[4] = e, d[5] = o, d[6] = i, d[7] = h, d[8] = c, d[9] = M, d[10] = s, d[11] = f, d[12] = l, d[13] = v, d[14] = b, d[15] = m, d
		}, set: function (t, n, a, r, u, e, o, i, h, c, M, s, f, l, v, b, m) {
			return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t[4] = e, t[5] = o, t[6] = i, t[7] = h, t[8] = c, t[9] = M, t[10] = s, t[11] = f, t[12] = l, t[13] = v, t[14] = b, t[15] = m, t
		}, identity: y, transpose: function (t, n) {
			if (t === n) {
				var a = n[1], r = n[2], u = n[3], e = n[6], o = n[7], i = n[11];
				t[1] = n[4], t[2] = n[8], t[3] = n[12], t[4] = a, t[6] = n[9], t[7] = n[13], t[8] = r, t[9] = e, t[11] = n[14], t[12] = u, t[13] = o, t[14] = i
			} else t[0] = n[0], t[1] = n[4], t[2] = n[8], t[3] = n[12], t[4] = n[1], t[5] = n[5], t[6] = n[9], t[7] = n[13], t[8] = n[2], t[9] = n[6], t[10] = n[10], t[11] = n[14], t[12] = n[3], t[13] = n[7], t[14] = n[11], t[15] = n[15];
			return t
		}, invert: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = n[6], c = n[7], M = n[8], s = n[9],
				f = n[10], l = n[11], v = n[12], b = n[13], m = n[14], d = n[15], p = a * i - r * o, x = a * h - u * o,
				q = a * c - e * o, w = r * h - u * i, y = r * c - e * i, g = u * c - e * h, A = M * b - s * v,
				R = M * m - f * v, z = M * d - l * v, P = s * m - f * b, j = s * d - l * b, I = f * d - l * m,
				S = p * I - x * j + q * P + w * z - y * R + g * A;
			return S ? (S = 1 / S, t[0] = (i * I - h * j + c * P) * S, t[1] = (u * j - r * I - e * P) * S, t[2] = (b * g - m * y + d * w) * S, t[3] = (f * y - s * g - l * w) * S, t[4] = (h * z - o * I - c * R) * S, t[5] = (a * I - u * z + e * R) * S, t[6] = (m * q - v * g - d * x) * S, t[7] = (M * g - f * q + l * x) * S, t[8] = (o * j - i * z + c * A) * S, t[9] = (r * z - a * j - e * A) * S, t[10] = (v * y - b * q + d * p) * S, t[11] = (s * q - M * y - l * p) * S, t[12] = (i * R - o * P - h * A) * S, t[13] = (a * P - r * R + u * A) * S, t[14] = (b * x - v * w - m * p) * S, t[15] = (M * w - s * x + f * p) * S, t) : null
		}, adjoint: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = n[4], i = n[5], h = n[6], c = n[7], M = n[8], s = n[9],
				f = n[10], l = n[11], v = n[12], b = n[13], m = n[14], d = n[15];
			return t[0] = i * (f * d - l * m) - s * (h * d - c * m) + b * (h * l - c * f), t[1] = -(r * (f * d - l * m) - s * (u * d - e * m) + b * (u * l - e * f)), t[2] = r * (h * d - c * m) - i * (u * d - e * m) + b * (u * c - e * h), t[3] = -(r * (h * l - c * f) - i * (u * l - e * f) + s * (u * c - e * h)), t[4] = -(o * (f * d - l * m) - M * (h * d - c * m) + v * (h * l - c * f)), t[5] = a * (f * d - l * m) - M * (u * d - e * m) + v * (u * l - e * f), t[6] = -(a * (h * d - c * m) - o * (u * d - e * m) + v * (u * c - e * h)), t[7] = a * (h * l - c * f) - o * (u * l - e * f) + M * (u * c - e * h), t[8] = o * (s * d - l * b) - M * (i * d - c * b) + v * (i * l - c * s), t[9] = -(a * (s * d - l * b) - M * (r * d - e * b) + v * (r * l - e * s)), t[10] = a * (i * d - c * b) - o * (r * d - e * b) + v * (r * c - e * i), t[11] = -(a * (i * l - c * s) - o * (r * l - e * s) + M * (r * c - e * i)), t[12] = -(o * (s * m - f * b) - M * (i * m - h * b) + v * (i * f - h * s)), t[13] = a * (s * m - f * b) - M * (r * m - u * b) + v * (r * f - u * s), t[14] = -(a * (i * m - h * b) - o * (r * m - u * b) + v * (r * h - u * i)), t[15] = a * (i * f - h * s) - o * (r * f - u * s) + M * (r * h - u * i), t
		}, determinant: function (t) {
			var n = t[0], a = t[1], r = t[2], u = t[3], e = t[4], o = t[5], i = t[6], h = t[7], c = t[8], M = t[9],
				s = t[10], f = t[11], l = t[12], v = t[13], b = t[14], m = t[15];
			return (n * o - a * e) * (s * m - f * b) - (n * i - r * e) * (M * m - f * v) + (n * h - u * e) * (M * b - s * v) + (a * i - r * o) * (c * m - f * l) - (a * h - u * o) * (c * b - s * l) + (r * h - u * i) * (c * v - M * l)
		}, multiply: g, translate: function (t, n, a) {
			var r, u, e, o, i, h, c, M, s, f, l, v, b = a[0], m = a[1], d = a[2];
			return n === t ? (t[12] = n[0] * b + n[4] * m + n[8] * d + n[12], t[13] = n[1] * b + n[5] * m + n[9] * d + n[13], t[14] = n[2] * b + n[6] * m + n[10] * d + n[14], t[15] = n[3] * b + n[7] * m + n[11] * d + n[15]) : (r = n[0], u = n[1], e = n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7], s = n[8], f = n[9], l = n[10], v = n[11], t[0] = r, t[1] = u, t[2] = e, t[3] = o, t[4] = i, t[5] = h, t[6] = c, t[7] = M, t[8] = s, t[9] = f, t[10] = l, t[11] = v, t[12] = r * b + i * m + s * d + n[12], t[13] = u * b + h * m + f * d + n[13], t[14] = e * b + c * m + l * d + n[14], t[15] = o * b + M * m + v * d + n[15]), t
		}, scale: function (t, n, a) {
			var r = a[0], u = a[1], e = a[2];
			return t[0] = n[0] * r, t[1] = n[1] * r, t[2] = n[2] * r, t[3] = n[3] * r, t[4] = n[4] * u, t[5] = n[5] * u, t[6] = n[6] * u, t[7] = n[7] * u, t[8] = n[8] * e, t[9] = n[9] * e, t[10] = n[10] * e, t[11] = n[11] * e, t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15], t
		}, rotate: function (t, a, r, u) {
			var e, o, i, h, c, M, s, f, l, v, b, m, d, p, x, q, w, y, g, A, R, z, P, j, I = u[0], S = u[1], E = u[2],
				O = Math.sqrt(I * I + S * S + E * E);
			return O < n ? null : (I *= O = 1 / O, S *= O, E *= O, e = Math.sin(r), i = 1 - (o = Math.cos(r)), h = a[0], c = a[1], M = a[2], s = a[3], f = a[4], l = a[5], v = a[6], b = a[7], m = a[8], d = a[9], p = a[10], x = a[11], q = I * I * i + o, w = S * I * i + E * e, y = E * I * i - S * e, g = I * S * i - E * e, A = S * S * i + o, R = E * S * i + I * e, z = I * E * i + S * e, P = S * E * i - I * e, j = E * E * i + o, t[0] = h * q + f * w + m * y, t[1] = c * q + l * w + d * y, t[2] = M * q + v * w + p * y, t[3] = s * q + b * w + x * y, t[4] = h * g + f * A + m * R, t[5] = c * g + l * A + d * R, t[6] = M * g + v * A + p * R, t[7] = s * g + b * A + x * R, t[8] = h * z + f * P + m * j, t[9] = c * z + l * P + d * j, t[10] = M * z + v * P + p * j, t[11] = s * z + b * P + x * j, a !== t && (t[12] = a[12], t[13] = a[13], t[14] = a[14], t[15] = a[15]), t)
		}, rotateX: function (t, n, a) {
			var r = Math.sin(a), u = Math.cos(a), e = n[4], o = n[5], i = n[6], h = n[7], c = n[8], M = n[9], s = n[10],
				f = n[11];
			return n !== t && (t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15]), t[4] = e * u + c * r, t[5] = o * u + M * r, t[6] = i * u + s * r, t[7] = h * u + f * r, t[8] = c * u - e * r, t[9] = M * u - o * r, t[10] = s * u - i * r, t[11] = f * u - h * r, t
		}, rotateY: function (t, n, a) {
			var r = Math.sin(a), u = Math.cos(a), e = n[0], o = n[1], i = n[2], h = n[3], c = n[8], M = n[9], s = n[10],
				f = n[11];
			return n !== t && (t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15]), t[0] = e * u - c * r, t[1] = o * u - M * r, t[2] = i * u - s * r, t[3] = h * u - f * r, t[8] = e * r + c * u, t[9] = o * r + M * u, t[10] = i * r + s * u, t[11] = h * r + f * u, t
		}, rotateZ: function (t, n, a) {
			var r = Math.sin(a), u = Math.cos(a), e = n[0], o = n[1], i = n[2], h = n[3], c = n[4], M = n[5], s = n[6],
				f = n[7];
			return n !== t && (t[8] = n[8], t[9] = n[9], t[10] = n[10], t[11] = n[11], t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15]), t[0] = e * u + c * r, t[1] = o * u + M * r, t[2] = i * u + s * r, t[3] = h * u + f * r, t[4] = c * u - e * r, t[5] = M * u - o * r, t[6] = s * u - i * r, t[7] = f * u - h * r, t
		}, fromTranslation: function (t, n) {
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = 1, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[10] = 1, t[11] = 0, t[12] = n[0], t[13] = n[1], t[14] = n[2], t[15] = 1, t
		}, fromScaling: function (t, n) {
			return t[0] = n[0], t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = n[1], t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[10] = n[2], t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
		}, fromRotation: function (t, a, r) {
			var u, e, o, i = r[0], h = r[1], c = r[2], M = Math.sqrt(i * i + h * h + c * c);
			return M < n ? null : (i *= M = 1 / M, h *= M, c *= M, u = Math.sin(a), o = 1 - (e = Math.cos(a)), t[0] = i * i * o + e, t[1] = h * i * o + c * u, t[2] = c * i * o - h * u, t[3] = 0, t[4] = i * h * o - c * u, t[5] = h * h * o + e, t[6] = c * h * o + i * u, t[7] = 0, t[8] = i * c * o + h * u, t[9] = h * c * o - i * u, t[10] = c * c * o + e, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t)
		}, fromXRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = 1, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = r, t[6] = a, t[7] = 0, t[8] = 0, t[9] = -a, t[10] = r, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
		}, fromYRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = r, t[1] = 0, t[2] = -a, t[3] = 0, t[4] = 0, t[5] = 1, t[6] = 0, t[7] = 0, t[8] = a, t[9] = 0, t[10] = r, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
		}, fromZRotation: function (t, n) {
			var a = Math.sin(n), r = Math.cos(n);
			return t[0] = r, t[1] = a, t[2] = 0, t[3] = 0, t[4] = -a, t[5] = r, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[10] = 1, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
		}, fromRotationTranslation: A, fromQuat2: function (t, n) {
			var r = new a(3), u = -n[0], e = -n[1], o = -n[2], i = n[3], h = n[4], c = n[5], M = n[6], s = n[7],
				f = u * u + e * e + o * o + i * i;
			return f > 0 ? (r[0] = 2 * (h * i + s * u + c * o - M * e) / f, r[1] = 2 * (c * i + s * e + M * u - h * o) / f, r[2] = 2 * (M * i + s * o + h * e - c * u) / f) : (r[0] = 2 * (h * i + s * u + c * o - M * e), r[1] = 2 * (c * i + s * e + M * u - h * o), r[2] = 2 * (M * i + s * o + h * e - c * u)), A(t, n, r), t
		}, getTranslation: R, getScaling: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[4], o = n[5], i = n[6], h = n[8], c = n[9], M = n[10];
			return t[0] = Math.sqrt(a * a + r * r + u * u), t[1] = Math.sqrt(e * e + o * o + i * i), t[2] = Math.sqrt(h * h + c * c + M * M), t
		}, getRotation: z, fromRotationTranslationScale: function (t, n, a, r) {
			var u = n[0], e = n[1], o = n[2], i = n[3], h = u + u, c = e + e, M = o + o, s = u * h, f = u * c,
				l = u * M, v = e * c, b = e * M, m = o * M, d = i * h, p = i * c, x = i * M, q = r[0], w = r[1],
				y = r[2];
			return t[0] = (1 - (v + m)) * q, t[1] = (f + x) * q, t[2] = (l - p) * q, t[3] = 0, t[4] = (f - x) * w, t[5] = (1 - (s + m)) * w, t[6] = (b + d) * w, t[7] = 0, t[8] = (l + p) * y, t[9] = (b - d) * y, t[10] = (1 - (s + v)) * y, t[11] = 0, t[12] = a[0], t[13] = a[1], t[14] = a[2], t[15] = 1, t
		}, fromRotationTranslationScaleOrigin: function (t, n, a, r, u) {
			var e = n[0], o = n[1], i = n[2], h = n[3], c = e + e, M = o + o, s = i + i, f = e * c, l = e * M,
				v = e * s, b = o * M, m = o * s, d = i * s, p = h * c, x = h * M, q = h * s, w = r[0], y = r[1],
				g = r[2], A = u[0], R = u[1], z = u[2], P = (1 - (b + d)) * w, j = (l + q) * w, I = (v - x) * w,
				S = (l - q) * y, E = (1 - (f + d)) * y, O = (m + p) * y, T = (v + x) * g, D = (m - p) * g,
				F = (1 - (f + b)) * g;
			return t[0] = P, t[1] = j, t[2] = I, t[3] = 0, t[4] = S, t[5] = E, t[6] = O, t[7] = 0, t[8] = T, t[9] = D, t[10] = F, t[11] = 0, t[12] = a[0] + A - (P * A + S * R + T * z), t[13] = a[1] + R - (j * A + E * R + D * z), t[14] = a[2] + z - (I * A + O * R + F * z), t[15] = 1, t
		}, fromQuat: function (t, n) {
			var a = n[0], r = n[1], u = n[2], e = n[3], o = a + a, i = r + r, h = u + u, c = a * o, M = r * o,
				s = r * i, f = u * o, l = u * i, v = u * h, b = e * o, m = e * i, d = e * h;
			return t[0] = 1 - s - v, t[1] = M + d, t[2] = f - m, t[3] = 0, t[4] = M - d, t[5] = 1 - c - v, t[6] = l + b, t[7] = 0, t[8] = f + m, t[9] = l - b, t[10] = 1 - c - s, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, t
		}, frustum: function (t, n, a, r, u, e, o) {
			var i = 1 / (a - n), h = 1 / (u - r), c = 1 / (e - o);
			return t[0] = 2 * e * i, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = 2 * e * h, t[6] = 0, t[7] = 0, t[8] = (a + n) * i, t[9] = (u + r) * h, t[10] = (o + e) * c, t[11] = -1, t[12] = 0, t[13] = 0, t[14] = o * e * 2 * c, t[15] = 0, t
		}, perspective: function (t, n, a, r, u) {
			var e, o = 1 / Math.tan(n / 2);
			return t[0] = o / a, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = o, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[11] = -1, t[12] = 0, t[13] = 0, t[15] = 0, null != u && u !== 1 / 0 ? (e = 1 / (r - u), t[10] = (u + r) * e, t[14] = 2 * u * r * e) : (t[10] = -1, t[14] = -2 * r), t
		}, perspectiveFromFieldOfView: function (t, n, a, r) {
			var u = Math.tan(n.upDegrees * Math.PI / 180), e = Math.tan(n.downDegrees * Math.PI / 180),
				o = Math.tan(n.leftDegrees * Math.PI / 180), i = Math.tan(n.rightDegrees * Math.PI / 180),
				h = 2 / (o + i), c = 2 / (u + e);
			return t[0] = h, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = c, t[6] = 0, t[7] = 0, t[8] = -(o - i) * h * .5, t[9] = (u - e) * c * .5, t[10] = r / (a - r), t[11] = -1, t[12] = 0, t[13] = 0, t[14] = r * a / (a - r), t[15] = 0, t
		}, ortho: function (t, n, a, r, u, e, o) {
			var i = 1 / (n - a), h = 1 / (r - u), c = 1 / (e - o);
			return t[0] = -2 * i, t[1] = 0, t[2] = 0, t[3] = 0, t[4] = 0, t[5] = -2 * h, t[6] = 0, t[7] = 0, t[8] = 0, t[9] = 0, t[10] = 2 * c, t[11] = 0, t[12] = (n + a) * i, t[13] = (u + r) * h, t[14] = (o + e) * c, t[15] = 1, t
		}, lookAt: function (t, a, r, u) {
			var e, o, i, h, c, M, s, f, l, v, b = a[0], m = a[1], d = a[2], p = u[0], x = u[1], q = u[2], w = r[0],
				g = r[1], A = r[2];
			return Math.abs(b - w) < n && Math.abs(m - g) < n && Math.abs(d - A) < n ? y(t) : (s = b - w, f = m - g, l = d - A, e = x * (l *= v = 1 / Math.sqrt(s * s + f * f + l * l)) - q * (f *= v), o = q * (s *= v) - p * l, i = p * f - x * s, (v = Math.sqrt(e * e + o * o + i * i)) ? (e *= v = 1 / v, o *= v, i *= v) : (e = 0, o = 0, i = 0), h = f * i - l * o, c = l * e - s * i, M = s * o - f * e, (v = Math.sqrt(h * h + c * c + M * M)) ? (h *= v = 1 / v, c *= v, M *= v) : (h = 0, c = 0, M = 0), t[0] = e, t[1] = h, t[2] = s, t[3] = 0, t[4] = o, t[5] = c, t[6] = f, t[7] = 0, t[8] = i, t[9] = M, t[10] = l, t[11] = 0, t[12] = -(e * b + o * m + i * d), t[13] = -(h * b + c * m + M * d), t[14] = -(s * b + f * m + l * d), t[15] = 1, t)
		}, targetTo: function (t, n, a, r) {
			var u = n[0], e = n[1], o = n[2], i = r[0], h = r[1], c = r[2], M = u - a[0], s = e - a[1], f = o - a[2],
				l = M * M + s * s + f * f;
			l > 0 && (M *= l = 1 / Math.sqrt(l), s *= l, f *= l);
			var v = h * f - c * s, b = c * M - i * f, m = i * s - h * M;
			return (l = v * v + b * b + m * m) > 0 && (v *= l = 1 / Math.sqrt(l), b *= l, m *= l), t[0] = v, t[1] = b, t[2] = m, t[3] = 0, t[4] = s * m - f * b, t[5] = f * v - M * m, t[6] = M * b - s * v, t[7] = 0, t[8] = M, t[9] = s, t[10] = f, t[11] = 0, t[12] = u, t[13] = e, t[14] = o, t[15] = 1, t
		}, str: function (t) {
			return "mat4(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ", " + t[4] + ", " + t[5] + ", " + t[6] + ", " + t[7] + ", " + t[8] + ", " + t[9] + ", " + t[10] + ", " + t[11] + ", " + t[12] + ", " + t[13] + ", " + t[14] + ", " + t[15] + ")"
		}, frob: function (t) {
			return Math.sqrt(Math.pow(t[0], 2) + Math.pow(t[1], 2) + Math.pow(t[2], 2) + Math.pow(t[3], 2) + Math.pow(t[4], 2) + Math.pow(t[5], 2) + Math.pow(t[6], 2) + Math.pow(t[7], 2) + Math.pow(t[8], 2) + Math.pow(t[9], 2) + Math.pow(t[10], 2) + Math.pow(t[11], 2) + Math.pow(t[12], 2) + Math.pow(t[13], 2) + Math.pow(t[14], 2) + Math.pow(t[15], 2))
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t[4] = n[4] + a[4], t[5] = n[5] + a[5], t[6] = n[6] + a[6], t[7] = n[7] + a[7], t[8] = n[8] + a[8], t[9] = n[9] + a[9], t[10] = n[10] + a[10], t[11] = n[11] + a[11], t[12] = n[12] + a[12], t[13] = n[13] + a[13], t[14] = n[14] + a[14], t[15] = n[15] + a[15], t
		}, subtract: P, multiplyScalar: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t[4] = n[4] * a, t[5] = n[5] * a, t[6] = n[6] * a, t[7] = n[7] * a, t[8] = n[8] * a, t[9] = n[9] * a, t[10] = n[10] * a, t[11] = n[11] * a, t[12] = n[12] * a, t[13] = n[13] * a, t[14] = n[14] * a, t[15] = n[15] * a, t
		}, multiplyScalarAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t[3] = n[3] + a[3] * r, t[4] = n[4] + a[4] * r, t[5] = n[5] + a[5] * r, t[6] = n[6] + a[6] * r, t[7] = n[7] + a[7] * r, t[8] = n[8] + a[8] * r, t[9] = n[9] + a[9] * r, t[10] = n[10] + a[10] * r, t[11] = n[11] + a[11] * r, t[12] = n[12] + a[12] * r, t[13] = n[13] + a[13] * r, t[14] = n[14] + a[14] * r, t[15] = n[15] + a[15] * r, t
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3] && t[4] === n[4] && t[5] === n[5] && t[6] === n[6] && t[7] === n[7] && t[8] === n[8] && t[9] === n[9] && t[10] === n[10] && t[11] === n[11] && t[12] === n[12] && t[13] === n[13] && t[14] === n[14] && t[15] === n[15]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = t[3], i = t[4], h = t[5], c = t[6], M = t[7], s = t[8], f = t[9],
				l = t[10], v = t[11], b = t[12], m = t[13], d = t[14], p = t[15], x = a[0], q = a[1], w = a[2],
				y = a[3], g = a[4], A = a[5], R = a[6], z = a[7], P = a[8], j = a[9], I = a[10], S = a[11], E = a[12],
				O = a[13], T = a[14], D = a[15];
			return Math.abs(r - x) <= n * Math.max(1, Math.abs(r), Math.abs(x)) && Math.abs(u - q) <= n * Math.max(1, Math.abs(u), Math.abs(q)) && Math.abs(e - w) <= n * Math.max(1, Math.abs(e), Math.abs(w)) && Math.abs(o - y) <= n * Math.max(1, Math.abs(o), Math.abs(y)) && Math.abs(i - g) <= n * Math.max(1, Math.abs(i), Math.abs(g)) && Math.abs(h - A) <= n * Math.max(1, Math.abs(h), Math.abs(A)) && Math.abs(c - R) <= n * Math.max(1, Math.abs(c), Math.abs(R)) && Math.abs(M - z) <= n * Math.max(1, Math.abs(M), Math.abs(z)) && Math.abs(s - P) <= n * Math.max(1, Math.abs(s), Math.abs(P)) && Math.abs(f - j) <= n * Math.max(1, Math.abs(f), Math.abs(j)) && Math.abs(l - I) <= n * Math.max(1, Math.abs(l), Math.abs(I)) && Math.abs(v - S) <= n * Math.max(1, Math.abs(v), Math.abs(S)) && Math.abs(b - E) <= n * Math.max(1, Math.abs(b), Math.abs(E)) && Math.abs(m - O) <= n * Math.max(1, Math.abs(m), Math.abs(O)) && Math.abs(d - T) <= n * Math.max(1, Math.abs(d), Math.abs(T)) && Math.abs(p - D) <= n * Math.max(1, Math.abs(p), Math.abs(D))
		}, mul: j, sub: I
	});

	function E() {
		var t = new a(3);
		return a != Float32Array && (t[0] = 0, t[1] = 0, t[2] = 0), t
	}

	function O(t) {
		var n = t[0], a = t[1], r = t[2];
		return Math.sqrt(n * n + a * a + r * r)
	}

	function T(t, n, r) {
		var u = new a(3);
		return u[0] = t, u[1] = n, u[2] = r, u
	}

	function D(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t
	}

	function F(t, n, a) {
		return t[0] = n[0] * a[0], t[1] = n[1] * a[1], t[2] = n[2] * a[2], t
	}

	function L(t, n, a) {
		return t[0] = n[0] / a[0], t[1] = n[1] / a[1], t[2] = n[2] / a[2], t
	}

	function V(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1], u = n[2] - t[2];
		return Math.sqrt(a * a + r * r + u * u)
	}

	function Q(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1], u = n[2] - t[2];
		return a * a + r * r + u * u
	}

	function Y(t) {
		var n = t[0], a = t[1], r = t[2];
		return n * n + a * a + r * r
	}

	function X(t, n) {
		var a = n[0], r = n[1], u = n[2], e = a * a + r * r + u * u;
		return e > 0 && (e = 1 / Math.sqrt(e)), t[0] = n[0] * e, t[1] = n[1] * e, t[2] = n[2] * e, t
	}

	function Z(t, n) {
		return t[0] * n[0] + t[1] * n[1] + t[2] * n[2]
	}

	function _(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = a[0], i = a[1], h = a[2];
		return t[0] = u * h - e * i, t[1] = e * o - r * h, t[2] = r * i - u * o, t
	}

	var B, N = D, k = F, U = L, W = V, C = Q, G = O, H = Y, J = (B = E(), function (t, n, a, r, u, e) {
		var o, i;
		for (n || (n = 3), a || (a = 0), i = r ? Math.min(r * n + a, t.length) : t.length, o = a; o < i; o += n) B[0] = t[o], B[1] = t[o + 1], B[2] = t[o + 2], u(B, B, e), t[o] = B[0], t[o + 1] = B[1], t[o + 2] = B[2];
		return t
	}), K = Object.freeze({
		create: E, clone: function (t) {
			var n = new a(3);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n
		}, length: O, fromValues: T, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t
		}, set: function (t, n, a, r) {
			return t[0] = n, t[1] = a, t[2] = r, t
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t
		}, subtract: D, multiply: F, divide: L, ceil: function (t, n) {
			return t[0] = Math.ceil(n[0]), t[1] = Math.ceil(n[1]), t[2] = Math.ceil(n[2]), t
		}, floor: function (t, n) {
			return t[0] = Math.floor(n[0]), t[1] = Math.floor(n[1]), t[2] = Math.floor(n[2]), t
		}, min: function (t, n, a) {
			return t[0] = Math.min(n[0], a[0]), t[1] = Math.min(n[1], a[1]), t[2] = Math.min(n[2], a[2]), t
		}, max: function (t, n, a) {
			return t[0] = Math.max(n[0], a[0]), t[1] = Math.max(n[1], a[1]), t[2] = Math.max(n[2], a[2]), t
		}, round: function (t, n) {
			return t[0] = Math.round(n[0]), t[1] = Math.round(n[1]), t[2] = Math.round(n[2]), t
		}, scale: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t
		}, scaleAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t
		}, distance: V, squaredDistance: Q, squaredLength: Y, negate: function (t, n) {
			return t[0] = -n[0], t[1] = -n[1], t[2] = -n[2], t
		}, inverse: function (t, n) {
			return t[0] = 1 / n[0], t[1] = 1 / n[1], t[2] = 1 / n[2], t
		}, normalize: X, dot: Z, cross: _, lerp: function (t, n, a, r) {
			var u = n[0], e = n[1], o = n[2];
			return t[0] = u + r * (a[0] - u), t[1] = e + r * (a[1] - e), t[2] = o + r * (a[2] - o), t
		}, hermite: function (t, n, a, r, u, e) {
			var o = e * e, i = o * (2 * e - 3) + 1, h = o * (e - 2) + e, c = o * (e - 1), M = o * (3 - 2 * e);
			return t[0] = n[0] * i + a[0] * h + r[0] * c + u[0] * M, t[1] = n[1] * i + a[1] * h + r[1] * c + u[1] * M, t[2] = n[2] * i + a[2] * h + r[2] * c + u[2] * M, t
		}, bezier: function (t, n, a, r, u, e) {
			var o = 1 - e, i = o * o, h = e * e, c = i * o, M = 3 * e * i, s = 3 * h * o, f = h * e;
			return t[0] = n[0] * c + a[0] * M + r[0] * s + u[0] * f, t[1] = n[1] * c + a[1] * M + r[1] * s + u[1] * f, t[2] = n[2] * c + a[2] * M + r[2] * s + u[2] * f, t
		}, random: function (t, n) {
			n = n || 1;
			var a = 2 * r() * Math.PI, u = 2 * r() - 1, e = Math.sqrt(1 - u * u) * n;
			return t[0] = Math.cos(a) * e, t[1] = Math.sin(a) * e, t[2] = u * n, t
		}, transformMat4: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = a[3] * r + a[7] * u + a[11] * e + a[15];
			return o = o || 1, t[0] = (a[0] * r + a[4] * u + a[8] * e + a[12]) / o, t[1] = (a[1] * r + a[5] * u + a[9] * e + a[13]) / o, t[2] = (a[2] * r + a[6] * u + a[10] * e + a[14]) / o, t
		}, transformMat3: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2];
			return t[0] = r * a[0] + u * a[3] + e * a[6], t[1] = r * a[1] + u * a[4] + e * a[7], t[2] = r * a[2] + u * a[5] + e * a[8], t
		}, transformQuat: function (t, n, a) {
			var r = a[0], u = a[1], e = a[2], o = a[3], i = n[0], h = n[1], c = n[2], M = u * c - e * h,
				s = e * i - r * c, f = r * h - u * i, l = u * f - e * s, v = e * M - r * f, b = r * s - u * M,
				m = 2 * o;
			return M *= m, s *= m, f *= m, l *= 2, v *= 2, b *= 2, t[0] = i + M + l, t[1] = h + s + v, t[2] = c + f + b, t
		}, rotateX: function (t, n, a, r) {
			var u = [], e = [];
			return u[0] = n[0] - a[0], u[1] = n[1] - a[1], u[2] = n[2] - a[2], e[0] = u[0], e[1] = u[1] * Math.cos(r) - u[2] * Math.sin(r), e[2] = u[1] * Math.sin(r) + u[2] * Math.cos(r), t[0] = e[0] + a[0], t[1] = e[1] + a[1], t[2] = e[2] + a[2], t
		}, rotateY: function (t, n, a, r) {
			var u = [], e = [];
			return u[0] = n[0] - a[0], u[1] = n[1] - a[1], u[2] = n[2] - a[2], e[0] = u[2] * Math.sin(r) + u[0] * Math.cos(r), e[1] = u[1], e[2] = u[2] * Math.cos(r) - u[0] * Math.sin(r), t[0] = e[0] + a[0], t[1] = e[1] + a[1], t[2] = e[2] + a[2], t
		}, rotateZ: function (t, n, a, r) {
			var u = [], e = [];
			return u[0] = n[0] - a[0], u[1] = n[1] - a[1], u[2] = n[2] - a[2], e[0] = u[0] * Math.cos(r) - u[1] * Math.sin(r), e[1] = u[0] * Math.sin(r) + u[1] * Math.cos(r), e[2] = u[2], t[0] = e[0] + a[0], t[1] = e[1] + a[1], t[2] = e[2] + a[2], t
		}, angle: function (t, n) {
			var a = T(t[0], t[1], t[2]), r = T(n[0], n[1], n[2]);
			X(a, a), X(r, r);
			var u = Z(a, r);
			return u > 1 ? 0 : u < -1 ? Math.PI : Math.acos(u)
		}, zero: function (t) {
			return t[0] = 0, t[1] = 0, t[2] = 0, t
		}, str: function (t) {
			return "vec3(" + t[0] + ", " + t[1] + ", " + t[2] + ")"
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = a[0], i = a[1], h = a[2];
			return Math.abs(r - o) <= n * Math.max(1, Math.abs(r), Math.abs(o)) && Math.abs(u - i) <= n * Math.max(1, Math.abs(u), Math.abs(i)) && Math.abs(e - h) <= n * Math.max(1, Math.abs(e), Math.abs(h))
		}, sub: N, mul: k, div: U, dist: W, sqrDist: C, len: G, sqrLen: H, forEach: J
	});

	function $() {
		var t = new a(4);
		return a != Float32Array && (t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 0), t
	}

	function tt(t) {
		var n = new a(4);
		return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n
	}

	function nt(t, n, r, u) {
		var e = new a(4);
		return e[0] = t, e[1] = n, e[2] = r, e[3] = u, e
	}

	function at(t, n) {
		return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t
	}

	function rt(t, n, a, r, u) {
		return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t
	}

	function ut(t, n, a) {
		return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t
	}

	function et(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t[2] = n[2] - a[2], t[3] = n[3] - a[3], t
	}

	function ot(t, n, a) {
		return t[0] = n[0] * a[0], t[1] = n[1] * a[1], t[2] = n[2] * a[2], t[3] = n[3] * a[3], t
	}

	function it(t, n, a) {
		return t[0] = n[0] / a[0], t[1] = n[1] / a[1], t[2] = n[2] / a[2], t[3] = n[3] / a[3], t
	}

	function ht(t, n, a) {
		return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t
	}

	function ct(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1], u = n[2] - t[2], e = n[3] - t[3];
		return Math.sqrt(a * a + r * r + u * u + e * e)
	}

	function Mt(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1], u = n[2] - t[2], e = n[3] - t[3];
		return a * a + r * r + u * u + e * e
	}

	function st(t) {
		var n = t[0], a = t[1], r = t[2], u = t[3];
		return Math.sqrt(n * n + a * a + r * r + u * u)
	}

	function ft(t) {
		var n = t[0], a = t[1], r = t[2], u = t[3];
		return n * n + a * a + r * r + u * u
	}

	function lt(t, n) {
		var a = n[0], r = n[1], u = n[2], e = n[3], o = a * a + r * r + u * u + e * e;
		return o > 0 && (o = 1 / Math.sqrt(o)), t[0] = a * o, t[1] = r * o, t[2] = u * o, t[3] = e * o, t
	}

	function vt(t, n) {
		return t[0] * n[0] + t[1] * n[1] + t[2] * n[2] + t[3] * n[3]
	}

	function bt(t, n, a, r) {
		var u = n[0], e = n[1], o = n[2], i = n[3];
		return t[0] = u + r * (a[0] - u), t[1] = e + r * (a[1] - e), t[2] = o + r * (a[2] - o), t[3] = i + r * (a[3] - i), t
	}

	function mt(t, n) {
		return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3]
	}

	function dt(t, a) {
		var r = t[0], u = t[1], e = t[2], o = t[3], i = a[0], h = a[1], c = a[2], M = a[3];
		return Math.abs(r - i) <= n * Math.max(1, Math.abs(r), Math.abs(i)) && Math.abs(u - h) <= n * Math.max(1, Math.abs(u), Math.abs(h)) && Math.abs(e - c) <= n * Math.max(1, Math.abs(e), Math.abs(c)) && Math.abs(o - M) <= n * Math.max(1, Math.abs(o), Math.abs(M))
	}

	var pt = et, xt = ot, qt = it, wt = ct, yt = Mt, gt = st, At = ft, Rt = function () {
		var t = $();
		return function (n, a, r, u, e, o) {
			var i, h;
			for (a || (a = 4), r || (r = 0), h = u ? Math.min(u * a + r, n.length) : n.length, i = r; i < h; i += a) t[0] = n[i], t[1] = n[i + 1], t[2] = n[i + 2], t[3] = n[i + 3], e(t, t, o), n[i] = t[0], n[i + 1] = t[1], n[i + 2] = t[2], n[i + 3] = t[3];
			return n
		}
	}(), zt = Object.freeze({
		create: $,
		clone: tt,
		fromValues: nt,
		copy: at,
		set: rt,
		add: ut,
		subtract: et,
		multiply: ot,
		divide: it,
		ceil: function (t, n) {
			return t[0] = Math.ceil(n[0]), t[1] = Math.ceil(n[1]), t[2] = Math.ceil(n[2]), t[3] = Math.ceil(n[3]), t
		},
		floor: function (t, n) {
			return t[0] = Math.floor(n[0]), t[1] = Math.floor(n[1]), t[2] = Math.floor(n[2]), t[3] = Math.floor(n[3]), t
		},
		min: function (t, n, a) {
			return t[0] = Math.min(n[0], a[0]), t[1] = Math.min(n[1], a[1]), t[2] = Math.min(n[2], a[2]), t[3] = Math.min(n[3], a[3]), t
		},
		max: function (t, n, a) {
			return t[0] = Math.max(n[0], a[0]), t[1] = Math.max(n[1], a[1]), t[2] = Math.max(n[2], a[2]), t[3] = Math.max(n[3], a[3]), t
		},
		round: function (t, n) {
			return t[0] = Math.round(n[0]), t[1] = Math.round(n[1]), t[2] = Math.round(n[2]), t[3] = Math.round(n[3]), t
		},
		scale: ht,
		scaleAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t[2] = n[2] + a[2] * r, t[3] = n[3] + a[3] * r, t
		},
		distance: ct,
		squaredDistance: Mt,
		length: st,
		squaredLength: ft,
		negate: function (t, n) {
			return t[0] = -n[0], t[1] = -n[1], t[2] = -n[2], t[3] = -n[3], t
		},
		inverse: function (t, n) {
			return t[0] = 1 / n[0], t[1] = 1 / n[1], t[2] = 1 / n[2], t[3] = 1 / n[3], t
		},
		normalize: lt,
		dot: vt,
		cross: function (t, n, a, r) {
			var u = a[0] * r[1] - a[1] * r[0], e = a[0] * r[2] - a[2] * r[0], o = a[0] * r[3] - a[3] * r[0],
				i = a[1] * r[2] - a[2] * r[1], h = a[1] * r[3] - a[3] * r[1], c = a[2] * r[3] - a[3] * r[2], M = n[0],
				s = n[1], f = n[2], l = n[3];
			return t[0] = s * c - f * h + l * i, t[1] = -M * c + f * o - l * e, t[2] = M * h - s * o + l * u, t[3] = -M * i + s * e - f * u, t
		},
		lerp: bt,
		random: function (t, n) {
			var a, u, e, o, i, h;
			n = n || 1;
			do {
				i = (a = 2 * r() - 1) * a + (u = 2 * r() - 1) * u
			} while (i >= 1);
			do {
				h = (e = 2 * r() - 1) * e + (o = 2 * r() - 1) * o
			} while (h >= 1);
			var c = Math.sqrt((1 - i) / h);
			return t[0] = n * a, t[1] = n * u, t[2] = n * e * c, t[3] = n * o * c, t
		},
		transformMat4: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3];
			return t[0] = a[0] * r + a[4] * u + a[8] * e + a[12] * o, t[1] = a[1] * r + a[5] * u + a[9] * e + a[13] * o, t[2] = a[2] * r + a[6] * u + a[10] * e + a[14] * o, t[3] = a[3] * r + a[7] * u + a[11] * e + a[15] * o, t
		},
		transformQuat: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = a[0], i = a[1], h = a[2], c = a[3], M = c * r + i * e - h * u,
				s = c * u + h * r - o * e, f = c * e + o * u - i * r, l = -o * r - i * u - h * e;
			return t[0] = M * c + l * -o + s * -h - f * -i, t[1] = s * c + l * -i + f * -o - M * -h, t[2] = f * c + l * -h + M * -i - s * -o, t[3] = n[3], t
		},
		zero: function (t) {
			return t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 0, t
		},
		str: function (t) {
			return "vec4(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ")"
		},
		exactEquals: mt,
		equals: dt,
		sub: pt,
		mul: xt,
		div: qt,
		dist: wt,
		sqrDist: yt,
		len: gt,
		sqrLen: At,
		forEach: Rt
	});

	function Pt() {
		var t = new a(4);
		return a != Float32Array && (t[0] = 0, t[1] = 0, t[2] = 0), t[3] = 1, t
	}

	function jt(t, n, a) {
		a *= .5;
		var r = Math.sin(a);
		return t[0] = r * n[0], t[1] = r * n[1], t[2] = r * n[2], t[3] = Math.cos(a), t
	}

	function It(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = a[0], h = a[1], c = a[2], M = a[3];
		return t[0] = r * M + o * i + u * c - e * h, t[1] = u * M + o * h + e * i - r * c, t[2] = e * M + o * c + r * h - u * i, t[3] = o * M - r * i - u * h - e * c, t
	}

	function St(t, n, a) {
		a *= .5;
		var r = n[0], u = n[1], e = n[2], o = n[3], i = Math.sin(a), h = Math.cos(a);
		return t[0] = r * h + o * i, t[1] = u * h + e * i, t[2] = e * h - u * i, t[3] = o * h - r * i, t
	}

	function Et(t, n, a) {
		a *= .5;
		var r = n[0], u = n[1], e = n[2], o = n[3], i = Math.sin(a), h = Math.cos(a);
		return t[0] = r * h - e * i, t[1] = u * h + o * i, t[2] = e * h + r * i, t[3] = o * h - u * i, t
	}

	function Ot(t, n, a) {
		a *= .5;
		var r = n[0], u = n[1], e = n[2], o = n[3], i = Math.sin(a), h = Math.cos(a);
		return t[0] = r * h + u * i, t[1] = u * h - r * i, t[2] = e * h + o * i, t[3] = o * h - e * i, t
	}

	function Tt(t, a, r, u) {
		var e, o, i, h, c, M = a[0], s = a[1], f = a[2], l = a[3], v = r[0], b = r[1], m = r[2], d = r[3];
		return (o = M * v + s * b + f * m + l * d) < 0 && (o = -o, v = -v, b = -b, m = -m, d = -d), 1 - o > n ? (e = Math.acos(o), i = Math.sin(e), h = Math.sin((1 - u) * e) / i, c = Math.sin(u * e) / i) : (h = 1 - u, c = u), t[0] = h * M + c * v, t[1] = h * s + c * b, t[2] = h * f + c * m, t[3] = h * l + c * d, t
	}

	function Dt(t, n) {
		var a, r = n[0] + n[4] + n[8];
		if (r > 0) a = Math.sqrt(r + 1), t[3] = .5 * a, a = .5 / a, t[0] = (n[5] - n[7]) * a, t[1] = (n[6] - n[2]) * a, t[2] = (n[1] - n[3]) * a; else {
			var u = 0;
			n[4] > n[0] && (u = 1), n[8] > n[3 * u + u] && (u = 2);
			var e = (u + 1) % 3, o = (u + 2) % 3;
			a = Math.sqrt(n[3 * u + u] - n[3 * e + e] - n[3 * o + o] + 1), t[u] = .5 * a, a = .5 / a, t[3] = (n[3 * e + o] - n[3 * o + e]) * a, t[e] = (n[3 * e + u] + n[3 * u + e]) * a, t[o] = (n[3 * o + u] + n[3 * u + o]) * a
		}
		return t
	}

	var Ft, Lt, Vt, Qt, Yt, Xt, Zt = tt, _t = nt, Bt = at, Nt = rt, kt = ut, Ut = It, Wt = ht, Ct = vt, Gt = bt,
		Ht = st, Jt = Ht, Kt = ft, $t = Kt, tn = lt, nn = mt, an = dt,
		rn = (Ft = E(), Lt = T(1, 0, 0), Vt = T(0, 1, 0), function (t, n, a) {
			var r = Z(n, a);
			return r < -.999999 ? (_(Ft, Lt, n), G(Ft) < 1e-6 && _(Ft, Vt, n), X(Ft, Ft), jt(t, Ft, Math.PI), t) : r > .999999 ? (t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 1, t) : (_(Ft, n, a), t[0] = Ft[0], t[1] = Ft[1], t[2] = Ft[2], t[3] = 1 + r, tn(t, t))
		}), un = (Qt = Pt(), Yt = Pt(), function (t, n, a, r, u, e) {
			return Tt(Qt, n, u, e), Tt(Yt, a, r, e), Tt(t, Qt, Yt, 2 * e * (1 - e)), t
		}), en = (Xt = m(), function (t, n, a, r) {
			return Xt[0] = a[0], Xt[3] = a[1], Xt[6] = a[2], Xt[1] = r[0], Xt[4] = r[1], Xt[7] = r[2], Xt[2] = -n[0], Xt[5] = -n[1], Xt[8] = -n[2], tn(t, Dt(t, Xt))
		}), on = Object.freeze({
			create: Pt,
			identity: function (t) {
				return t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 1, t
			},
			setAxisAngle: jt,
			getAxisAngle: function (t, a) {
				var r = 2 * Math.acos(a[3]), u = Math.sin(r / 2);
				return u > n ? (t[0] = a[0] / u, t[1] = a[1] / u, t[2] = a[2] / u) : (t[0] = 1, t[1] = 0, t[2] = 0), r
			},
			multiply: It,
			rotateX: St,
			rotateY: Et,
			rotateZ: Ot,
			calculateW: function (t, n) {
				var a = n[0], r = n[1], u = n[2];
				return t[0] = a, t[1] = r, t[2] = u, t[3] = Math.sqrt(Math.abs(1 - a * a - r * r - u * u)), t
			},
			slerp: Tt,
			random: function (t) {
				var n = r(), a = r(), u = r(), e = Math.sqrt(1 - n), o = Math.sqrt(n);
				return t[0] = e * Math.sin(2 * Math.PI * a), t[1] = e * Math.cos(2 * Math.PI * a), t[2] = o * Math.sin(2 * Math.PI * u), t[3] = o * Math.cos(2 * Math.PI * u), t
			},
			invert: function (t, n) {
				var a = n[0], r = n[1], u = n[2], e = n[3], o = a * a + r * r + u * u + e * e, i = o ? 1 / o : 0;
				return t[0] = -a * i, t[1] = -r * i, t[2] = -u * i, t[3] = e * i, t
			},
			conjugate: function (t, n) {
				return t[0] = -n[0], t[1] = -n[1], t[2] = -n[2], t[3] = n[3], t
			},
			fromMat3: Dt,
			fromEuler: function (t, n, a, r) {
				var u = .5 * Math.PI / 180;
				n *= u, a *= u, r *= u;
				var e = Math.sin(n), o = Math.cos(n), i = Math.sin(a), h = Math.cos(a), c = Math.sin(r), M = Math.cos(r);
				return t[0] = e * h * M - o * i * c, t[1] = o * i * M + e * h * c, t[2] = o * h * c - e * i * M, t[3] = o * h * M + e * i * c, t
			},
			str: function (t) {
				return "quat(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ")"
			},
			clone: Zt,
			fromValues: _t,
			copy: Bt,
			set: Nt,
			add: kt,
			mul: Ut,
			scale: Wt,
			dot: Ct,
			lerp: Gt,
			length: Ht,
			len: Jt,
			squaredLength: Kt,
			sqrLen: $t,
			normalize: tn,
			exactEquals: nn,
			equals: an,
			rotationTo: rn,
			sqlerp: un,
			setAxes: en
		});

	function hn(t, n, a) {
		var r = .5 * a[0], u = .5 * a[1], e = .5 * a[2], o = n[0], i = n[1], h = n[2], c = n[3];
		return t[0] = o, t[1] = i, t[2] = h, t[3] = c, t[4] = r * c + u * h - e * i, t[5] = u * c + e * o - r * h, t[6] = e * c + r * i - u * o, t[7] = -r * o - u * i - e * h, t
	}

	function cn(t, n) {
		return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t
	}

	var Mn = Bt;
	var sn = Bt;

	function fn(t, n, a) {
		var r = n[0], u = n[1], e = n[2], o = n[3], i = a[4], h = a[5], c = a[6], M = a[7], s = n[4], f = n[5],
			l = n[6], v = n[7], b = a[0], m = a[1], d = a[2], p = a[3];
		return t[0] = r * p + o * b + u * d - e * m, t[1] = u * p + o * m + e * b - r * d, t[2] = e * p + o * d + r * m - u * b, t[3] = o * p - r * b - u * m - e * d, t[4] = r * M + o * i + u * c - e * h + s * p + v * b + f * d - l * m, t[5] = u * M + o * h + e * i - r * c + f * p + v * m + l * b - s * d, t[6] = e * M + o * c + r * h - u * i + l * p + v * d + s * m - f * b, t[7] = o * M - r * i - u * h - e * c + v * p - s * b - f * m - l * d, t
	}

	var ln = fn;
	var vn = Ct;
	var bn = Ht, mn = bn, dn = Kt, pn = dn;
	var xn = Object.freeze({
		create: function () {
			var t = new a(8);
			return a != Float32Array && (t[0] = 0, t[1] = 0, t[2] = 0, t[4] = 0, t[5] = 0, t[6] = 0, t[7] = 0), t[3] = 1, t
		}, clone: function (t) {
			var n = new a(8);
			return n[0] = t[0], n[1] = t[1], n[2] = t[2], n[3] = t[3], n[4] = t[4], n[5] = t[5], n[6] = t[6], n[7] = t[7], n
		}, fromValues: function (t, n, r, u, e, o, i, h) {
			var c = new a(8);
			return c[0] = t, c[1] = n, c[2] = r, c[3] = u, c[4] = e, c[5] = o, c[6] = i, c[7] = h, c
		}, fromRotationTranslationValues: function (t, n, r, u, e, o, i) {
			var h = new a(8);
			h[0] = t, h[1] = n, h[2] = r, h[3] = u;
			var c = .5 * e, M = .5 * o, s = .5 * i;
			return h[4] = c * u + M * r - s * n, h[5] = M * u + s * t - c * r, h[6] = s * u + c * n - M * t, h[7] = -c * t - M * n - s * r, h
		}, fromRotationTranslation: hn, fromTranslation: function (t, n) {
			return t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 1, t[4] = .5 * n[0], t[5] = .5 * n[1], t[6] = .5 * n[2], t[7] = 0, t
		}, fromRotation: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = 0, t[5] = 0, t[6] = 0, t[7] = 0, t
		}, fromMat4: function (t, n) {
			var r = Pt();
			z(r, n);
			var u = new a(3);
			return R(u, n), hn(t, r, u), t
		}, copy: cn, identity: function (t) {
			return t[0] = 0, t[1] = 0, t[2] = 0, t[3] = 1, t[4] = 0, t[5] = 0, t[6] = 0, t[7] = 0, t
		}, set: function (t, n, a, r, u, e, o, i, h) {
			return t[0] = n, t[1] = a, t[2] = r, t[3] = u, t[4] = e, t[5] = o, t[6] = i, t[7] = h, t
		}, getReal: Mn, getDual: function (t, n) {
			return t[0] = n[4], t[1] = n[5], t[2] = n[6], t[3] = n[7], t
		}, setReal: sn, setDual: function (t, n) {
			return t[4] = n[0], t[5] = n[1], t[6] = n[2], t[7] = n[3], t
		}, getTranslation: function (t, n) {
			var a = n[4], r = n[5], u = n[6], e = n[7], o = -n[0], i = -n[1], h = -n[2], c = n[3];
			return t[0] = 2 * (a * c + e * o + r * h - u * i), t[1] = 2 * (r * c + e * i + u * o - a * h), t[2] = 2 * (u * c + e * h + a * i - r * o), t
		}, translate: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = .5 * a[0], h = .5 * a[1], c = .5 * a[2], M = n[4], s = n[5],
				f = n[6], l = n[7];
			return t[0] = r, t[1] = u, t[2] = e, t[3] = o, t[4] = o * i + u * c - e * h + M, t[5] = o * h + e * i - r * c + s, t[6] = o * c + r * h - u * i + f, t[7] = -r * i - u * h - e * c + l, t
		}, rotateX: function (t, n, a) {
			var r = -n[0], u = -n[1], e = -n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7],
				s = i * o + M * r + h * e - c * u, f = h * o + M * u + c * r - i * e, l = c * o + M * e + i * u - h * r,
				v = M * o - i * r - h * u - c * e;
			return St(t, n, a), r = t[0], u = t[1], e = t[2], o = t[3], t[4] = s * o + v * r + f * e - l * u, t[5] = f * o + v * u + l * r - s * e, t[6] = l * o + v * e + s * u - f * r, t[7] = v * o - s * r - f * u - l * e, t
		}, rotateY: function (t, n, a) {
			var r = -n[0], u = -n[1], e = -n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7],
				s = i * o + M * r + h * e - c * u, f = h * o + M * u + c * r - i * e, l = c * o + M * e + i * u - h * r,
				v = M * o - i * r - h * u - c * e;
			return Et(t, n, a), r = t[0], u = t[1], e = t[2], o = t[3], t[4] = s * o + v * r + f * e - l * u, t[5] = f * o + v * u + l * r - s * e, t[6] = l * o + v * e + s * u - f * r, t[7] = v * o - s * r - f * u - l * e, t
		}, rotateZ: function (t, n, a) {
			var r = -n[0], u = -n[1], e = -n[2], o = n[3], i = n[4], h = n[5], c = n[6], M = n[7],
				s = i * o + M * r + h * e - c * u, f = h * o + M * u + c * r - i * e, l = c * o + M * e + i * u - h * r,
				v = M * o - i * r - h * u - c * e;
			return Ot(t, n, a), r = t[0], u = t[1], e = t[2], o = t[3], t[4] = s * o + v * r + f * e - l * u, t[5] = f * o + v * u + l * r - s * e, t[6] = l * o + v * e + s * u - f * r, t[7] = v * o - s * r - f * u - l * e, t
		}, rotateByQuatAppend: function (t, n, a) {
			var r = a[0], u = a[1], e = a[2], o = a[3], i = n[0], h = n[1], c = n[2], M = n[3];
			return t[0] = i * o + M * r + h * e - c * u, t[1] = h * o + M * u + c * r - i * e, t[2] = c * o + M * e + i * u - h * r, t[3] = M * o - i * r - h * u - c * e, i = n[4], h = n[5], c = n[6], M = n[7], t[4] = i * o + M * r + h * e - c * u, t[5] = h * o + M * u + c * r - i * e, t[6] = c * o + M * e + i * u - h * r, t[7] = M * o - i * r - h * u - c * e, t
		}, rotateByQuatPrepend: function (t, n, a) {
			var r = n[0], u = n[1], e = n[2], o = n[3], i = a[0], h = a[1], c = a[2], M = a[3];
			return t[0] = r * M + o * i + u * c - e * h, t[1] = u * M + o * h + e * i - r * c, t[2] = e * M + o * c + r * h - u * i, t[3] = o * M - r * i - u * h - e * c, i = a[4], h = a[5], c = a[6], M = a[7], t[4] = r * M + o * i + u * c - e * h, t[5] = u * M + o * h + e * i - r * c, t[6] = e * M + o * c + r * h - u * i, t[7] = o * M - r * i - u * h - e * c, t
		}, rotateAroundAxis: function (t, a, r, u) {
			if (Math.abs(u) < n) return cn(t, a);
			var e = Math.sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);
			u *= .5;
			var o = Math.sin(u), i = o * r[0] / e, h = o * r[1] / e, c = o * r[2] / e, M = Math.cos(u), s = a[0],
				f = a[1], l = a[2], v = a[3];
			t[0] = s * M + v * i + f * c - l * h, t[1] = f * M + v * h + l * i - s * c, t[2] = l * M + v * c + s * h - f * i, t[3] = v * M - s * i - f * h - l * c;
			var b = a[4], m = a[5], d = a[6], p = a[7];
			return t[4] = b * M + p * i + m * c - d * h, t[5] = m * M + p * h + d * i - b * c, t[6] = d * M + p * c + b * h - m * i, t[7] = p * M - b * i - m * h - d * c, t
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t[2] = n[2] + a[2], t[3] = n[3] + a[3], t[4] = n[4] + a[4], t[5] = n[5] + a[5], t[6] = n[6] + a[6], t[7] = n[7] + a[7], t
		}, multiply: fn, mul: ln, scale: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t[2] = n[2] * a, t[3] = n[3] * a, t[4] = n[4] * a, t[5] = n[5] * a, t[6] = n[6] * a, t[7] = n[7] * a, t
		}, dot: vn, lerp: function (t, n, a, r) {
			var u = 1 - r;
			return vn(n, a) < 0 && (r = -r), t[0] = n[0] * u + a[0] * r, t[1] = n[1] * u + a[1] * r, t[2] = n[2] * u + a[2] * r, t[3] = n[3] * u + a[3] * r, t[4] = n[4] * u + a[4] * r, t[5] = n[5] * u + a[5] * r, t[6] = n[6] * u + a[6] * r, t[7] = n[7] * u + a[7] * r, t
		}, invert: function (t, n) {
			var a = dn(n);
			return t[0] = -n[0] / a, t[1] = -n[1] / a, t[2] = -n[2] / a, t[3] = n[3] / a, t[4] = -n[4] / a, t[5] = -n[5] / a, t[6] = -n[6] / a, t[7] = n[7] / a, t
		}, conjugate: function (t, n) {
			return t[0] = -n[0], t[1] = -n[1], t[2] = -n[2], t[3] = n[3], t[4] = -n[4], t[5] = -n[5], t[6] = -n[6], t[7] = n[7], t
		}, length: bn, len: mn, squaredLength: dn, sqrLen: pn, normalize: function (t, n) {
			var a = dn(n);
			if (a > 0) {
				a = Math.sqrt(a);
				var r = n[0] / a, u = n[1] / a, e = n[2] / a, o = n[3] / a, i = n[4], h = n[5], c = n[6], M = n[7],
					s = r * i + u * h + e * c + o * M;
				t[0] = r, t[1] = u, t[2] = e, t[3] = o, t[4] = (i - r * s) / a, t[5] = (h - u * s) / a, t[6] = (c - e * s) / a, t[7] = (M - o * s) / a
			}
			return t
		}, str: function (t) {
			return "quat2(" + t[0] + ", " + t[1] + ", " + t[2] + ", " + t[3] + ", " + t[4] + ", " + t[5] + ", " + t[6] + ", " + t[7] + ")"
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1] && t[2] === n[2] && t[3] === n[3] && t[4] === n[4] && t[5] === n[5] && t[6] === n[6] && t[7] === n[7]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = t[2], o = t[3], i = t[4], h = t[5], c = t[6], M = t[7], s = a[0], f = a[1],
				l = a[2], v = a[3], b = a[4], m = a[5], d = a[6], p = a[7];
			return Math.abs(r - s) <= n * Math.max(1, Math.abs(r), Math.abs(s)) && Math.abs(u - f) <= n * Math.max(1, Math.abs(u), Math.abs(f)) && Math.abs(e - l) <= n * Math.max(1, Math.abs(e), Math.abs(l)) && Math.abs(o - v) <= n * Math.max(1, Math.abs(o), Math.abs(v)) && Math.abs(i - b) <= n * Math.max(1, Math.abs(i), Math.abs(b)) && Math.abs(h - m) <= n * Math.max(1, Math.abs(h), Math.abs(m)) && Math.abs(c - d) <= n * Math.max(1, Math.abs(c), Math.abs(d)) && Math.abs(M - p) <= n * Math.max(1, Math.abs(M), Math.abs(p))
		}
	});

	function qn() {
		var t = new a(2);
		return a != Float32Array && (t[0] = 0, t[1] = 0), t
	}

	function wn(t, n, a) {
		return t[0] = n[0] - a[0], t[1] = n[1] - a[1], t
	}

	function yn(t, n, a) {
		return t[0] = n[0] * a[0], t[1] = n[1] * a[1], t
	}

	function gn(t, n, a) {
		return t[0] = n[0] / a[0], t[1] = n[1] / a[1], t
	}

	function An(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1];
		return Math.sqrt(a * a + r * r)
	}

	function Rn(t, n) {
		var a = n[0] - t[0], r = n[1] - t[1];
		return a * a + r * r
	}

	function zn(t) {
		var n = t[0], a = t[1];
		return Math.sqrt(n * n + a * a)
	}

	function Pn(t) {
		var n = t[0], a = t[1];
		return n * n + a * a
	}

	var jn = zn, In = wn, Sn = yn, En = gn, On = An, Tn = Rn, Dn = Pn, Fn = function () {
		var t = qn();
		return function (n, a, r, u, e, o) {
			var i, h;
			for (a || (a = 2), r || (r = 0), h = u ? Math.min(u * a + r, n.length) : n.length, i = r; i < h; i += a) t[0] = n[i], t[1] = n[i + 1], e(t, t, o), n[i] = t[0], n[i + 1] = t[1];
			return n
		}
	}(), Ln = Object.freeze({
		create: qn, clone: function (t) {
			var n = new a(2);
			return n[0] = t[0], n[1] = t[1], n
		}, fromValues: function (t, n) {
			var r = new a(2);
			return r[0] = t, r[1] = n, r
		}, copy: function (t, n) {
			return t[0] = n[0], t[1] = n[1], t
		}, set: function (t, n, a) {
			return t[0] = n, t[1] = a, t
		}, add: function (t, n, a) {
			return t[0] = n[0] + a[0], t[1] = n[1] + a[1], t
		}, subtract: wn, multiply: yn, divide: gn, ceil: function (t, n) {
			return t[0] = Math.ceil(n[0]), t[1] = Math.ceil(n[1]), t
		}, floor: function (t, n) {
			return t[0] = Math.floor(n[0]), t[1] = Math.floor(n[1]), t
		}, min: function (t, n, a) {
			return t[0] = Math.min(n[0], a[0]), t[1] = Math.min(n[1], a[1]), t
		}, max: function (t, n, a) {
			return t[0] = Math.max(n[0], a[0]), t[1] = Math.max(n[1], a[1]), t
		}, round: function (t, n) {
			return t[0] = Math.round(n[0]), t[1] = Math.round(n[1]), t
		}, scale: function (t, n, a) {
			return t[0] = n[0] * a, t[1] = n[1] * a, t
		}, scaleAndAdd: function (t, n, a, r) {
			return t[0] = n[0] + a[0] * r, t[1] = n[1] + a[1] * r, t
		}, distance: An, squaredDistance: Rn, length: zn, squaredLength: Pn, negate: function (t, n) {
			return t[0] = -n[0], t[1] = -n[1], t
		}, inverse: function (t, n) {
			return t[0] = 1 / n[0], t[1] = 1 / n[1], t
		}, normalize: function (t, n) {
			var a = n[0], r = n[1], u = a * a + r * r;
			return u > 0 && (u = 1 / Math.sqrt(u)), t[0] = n[0] * u, t[1] = n[1] * u, t
		}, dot: function (t, n) {
			return t[0] * n[0] + t[1] * n[1]
		}, cross: function (t, n, a) {
			var r = n[0] * a[1] - n[1] * a[0];
			return t[0] = t[1] = 0, t[2] = r, t
		}, lerp: function (t, n, a, r) {
			var u = n[0], e = n[1];
			return t[0] = u + r * (a[0] - u), t[1] = e + r * (a[1] - e), t
		}, random: function (t, n) {
			n = n || 1;
			var a = 2 * r() * Math.PI;
			return t[0] = Math.cos(a) * n, t[1] = Math.sin(a) * n, t
		}, transformMat2: function (t, n, a) {
			var r = n[0], u = n[1];
			return t[0] = a[0] * r + a[2] * u, t[1] = a[1] * r + a[3] * u, t
		}, transformMat2d: function (t, n, a) {
			var r = n[0], u = n[1];
			return t[0] = a[0] * r + a[2] * u + a[4], t[1] = a[1] * r + a[3] * u + a[5], t
		}, transformMat3: function (t, n, a) {
			var r = n[0], u = n[1];
			return t[0] = a[0] * r + a[3] * u + a[6], t[1] = a[1] * r + a[4] * u + a[7], t
		}, transformMat4: function (t, n, a) {
			var r = n[0], u = n[1];
			return t[0] = a[0] * r + a[4] * u + a[12], t[1] = a[1] * r + a[5] * u + a[13], t
		}, rotate: function (t, n, a, r) {
			var u = n[0] - a[0], e = n[1] - a[1], o = Math.sin(r), i = Math.cos(r);
			return t[0] = u * i - e * o + a[0], t[1] = u * o + e * i + a[1], t
		}, angle: function (t, n) {
			var a = t[0], r = t[1], u = n[0], e = n[1], o = a * a + r * r;
			o > 0 && (o = 1 / Math.sqrt(o));
			var i = u * u + e * e;
			i > 0 && (i = 1 / Math.sqrt(i));
			var h = (a * u + r * e) * o * i;
			return h > 1 ? 0 : h < -1 ? Math.PI : Math.acos(h)
		}, zero: function (t) {
			return t[0] = 0, t[1] = 0, t
		}, str: function (t) {
			return "vec2(" + t[0] + ", " + t[1] + ")"
		}, exactEquals: function (t, n) {
			return t[0] === n[0] && t[1] === n[1]
		}, equals: function (t, a) {
			var r = t[0], u = t[1], e = a[0], o = a[1];
			return Math.abs(r - e) <= n * Math.max(1, Math.abs(r), Math.abs(e)) && Math.abs(u - o) <= n * Math.max(1, Math.abs(u), Math.abs(o))
		}, len: jn, sub: In, mul: Sn, div: En, dist: On, sqrDist: Tn, sqrLen: Dn, forEach: Fn
	});
	t.glMatrix = e, t.mat2 = M, t.mat2d = b, t.mat3 = w, t.mat4 = S, t.quat = on, t.quat2 = xn, t.vec2 = Ln, t.vec3 = K, t.vec4 = zt, Object.defineProperty(t, "__esModule", {value: !0})
});
for (var k in glMatrix) {
	if (glMatrix.hasOwnProperty(k) && k != 'glMatrix') {
		window[k] = glMatrix[k]
	}
}