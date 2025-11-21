import streamlit as st
import pandas as pd
import database
import auth

# Configuración de la página (¡llamarla primero!)
st.set_page_config(page_title="Gestor de Centros", layout="wide", initial_sidebar_state="collapsed")

# --- FUNCIÓN DE LOGIN ---
def login_screen():
    """
    Muestra la pantalla de inicio de sesión y gestiona el login.
    """
    st.title("Gestor de Centros Educativos 🇨🇷")
    st.header("Inicio de Sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        user_data = database.get_user(username)
        if user_data:
            if user_data.get("is_locked"):
                st.error("Este usuario ha sido bloqueado por demasiados intentos fallidos. Solicite al administrador el cambio y desbloqueo de contraseña.")
                return
            if auth.check_password(password, user_data["password_hash"]):
                # Login exitoso
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_data["id"]
                st.session_state["username"] = user_data["username"]
                st.session_state["role"] = user_data["role"]
                st.session_state["full_name"] = user_data["full_name"]
                database.reset_failed_attempts(username)
                st.rerun()
            else:
                database.increment_failed_attempts(username)
                user_data = database.get_user(username)  # refrescar datos
                if user_data.get("is_locked"):
                    st.error("Usuario bloqueado tras 5 intentos fallidos. Solicite al administrador el cambio y desbloqueo de contraseña.")
                else:
                    st.error("Usuario o contraseña incorrectos")
        else:
            st.toast("Usuario o contraseña incorrectos", icon="❌")

# --- APLICACIÓN PRINCIPAL (POST-LOGIN) ---
def main_app():
        # --- Cierre de sesión por inactividad ---
        import time
        INACTIVITY_TIMEOUT = 900  # 15 minutos en segundos
        now = int(time.time())
        last_active = st.session_state.get("last_active", now)
        if now - last_active > INACTIVITY_TIMEOUT:
            st.session_state.clear()
            st.warning("Sesión cerrada por inactividad. Por favor, inicie sesión nuevamente.")
            st.stop()
        st.session_state["last_active"] = now
        def main_app():
            # --- Cierre de sesión por inactividad ---
            import time
            INACTIVITY_TIMEOUT = 900  # 15 minutos en segundos
            now = int(time.time())
            last_active = st.session_state.get("last_active", now)
            if now - last_active > INACTIVITY_TIMEOUT:
                st.session_state.clear()
                st.warning("Sesión cerrada por inactividad. Por favor, inicie sesión nuevamente.")
                st.stop()
            st.session_state["last_active"] = now
        """
        Lógica principal de la aplicación tras el login.
        """
        # Intentar importar las vistas de forma perezosa (evita fallos en import)
        def mostrar_error_importacion(vista, error):
            st.error(f"La vista de {vista} no está disponible debido a un error de importación: {error}. Revisa las dependencias.")
        # ...resto del código..."""
    Lógica principal de la aplicación tras el login.
    """
    # Intentar importar las vistas de forma perezosa (evita fallos en import)
    def mostrar_error_importacion(vista, error):
        st.error(f"La vista de {vista} no está disponible debido a un error de importación: {error}. Revisa las dependencias.")

    try:
        import admin_view
    except Exception as e:
        admin_view = None
        mostrar_error_importacion("administrador", e)

    try:
        import operator_view
    except Exception as e:
        operator_view = None
        mostrar_error_importacion("operador", e)

    # Configurar la barra lateral
    st.sidebar.title(f"Hola, {st.session_state['full_name']}")
    st.sidebar.caption(f"Rol: {st.session_state['role'].capitalize()}")
    # Selector de tema visual
    theme = st.sidebar.radio("Tema visual", ["Claro", "Oscuro"], index=0, key="theme_selector")
    if theme == "Oscuro":
        st.markdown("""
            <style>
            body, .stApp { background-color: #222 !important; color: #eee !important; }
            .st-bb, .st-c6, .st-cg, .st-cj, .st-cq, .st-cr, .st-cs, .st-ct, .st-cu, .st-cv, .st-cw, .st-cx, .st-cy, .st-cz, .st-da, .st-db, .st-dc, .st-dd, .st-de, .st-df, .st-dg, .st-dh, .st-di, .st-dj, .st-dk, .st-dl, .st-dm, .st-dn, .st-do, .st-dp, .st-dq, .st-dr, .st-ds, .st-dt, .st-du, .st-dv, .st-dw, .st-dx, .st-dy, .st-dz, .st-e0, .st-e1, .st-e2, .st-e3, .st-e4, .st-e5, .st-e6, .st-e7, .st-e8, .st-e9, .st-ea, .st-eb, .st-ec, .st-ed, .st-ee, .st-ef, .st-eg, .st-eh, .st-ei, .st-ej, .st-ek, .st-el, .st-em, .st-en, .st-eo, .st-ep, .st-eq, .st-er, .st-es, .st-et, .st-eu, .st-ev, .st-ew, .st-ex, .st-ey, .st-ez, .st-f0, .st-f1, .st-f2, .st-f3, .st-f4, .st-f5, .st-f6, .st-f7, .st-f8, .st-f9, .st-fa, .st-fb, .st-fc, .st-fd, .st-fe, .st-ff, .st-fg, .st-fh, .st-fi, .st-fj, .st-fk, .st-fl, .st-fm, .st-fn, .st-fo, .st-fp, .st-fq, .st-fr, .st-fs, .st-ft, .st-fu, .st-fv, .st-fw, .st-fx, .st-fy, .st-fz, .st-g0, .st-g1, .st-g2, .st-g3, .st-g4, .st-g5, .st-g6, .st-g7, .st-g8, .st-g9, .st-ga, .st-gb, .st-gc, .st-gd, .st-ge, .st-gf, .st-gg, .st-gh, .st-gi, .st-gj, .st-gk, .st-gl, .st-gm, .st-gn, .st-go, .st-gp, .st-gq, .st-gr, .st-gs, .st-gt, .st-gu, .st-gv, .st-gw, .st-gx, .st-gy, .st-gz, .st-h0, .st-h1, .st-h2, .st-h3, .st-h4, .st-h5, .st-h6, .st-h7, .st-h8, .st-h9, .st-ha, .st-hb, .st-hc, .st-hd, .st-he, .st-hf, .st-hg, .st-hh, .st-hi, .st-hj, .st-hk, .st-hl, .st-hm, .st-hn, .st-ho, .st-hp, .st-hq, .st-hr, .st-hs, .st-ht, .st-hu, .st-hv, .st-hw, .st-hx, .st-hy, .st-hz, .st-i0, .st-i1, .st-i2, .st-i3, .st-i4, .st-i5, .st-i6, .st-i7, .st-i8, .st-i9, .st-ia, .st-ib, .st-ic, .st-id, .st-ie, .st-if, .st-ig, .st-ih, .st-ii, .st-ij, .st-ik, .st-il, .st-im, .st-in, .st-io, .st-ip, .st-iq, .st-ir, .st-is, .st-it, .st-iu, .st-iv, .st-iw, .st-ix, .st-iy, .st-iz, .st-j0, .st-j1, .st-j2, .st-j3, .st-j4, .st-j5, .st-j6, .st-j7, .st-j8, .st-j9, .st-ja, .st-jb, .st-jc, .st-jd, .st-je, .st-jf, .st-jg, .st-jh, .st-ji, .st-jj, .st-jk, .st-jl, .st-jm, .st-jn, .st-jo, .st-jp, .st-jq, .st-jr, .st-js, .st-jt, .st-ju, .st-jv, .st-jw, .st-jx, .st-jy, .st-jz, .st-k0, .st-k1, .st-k2, .st-k3, .st-k4, .st-k5, .st-k6, .st-k7, .st-k8, .st-k9, .st-ka, .st-kb, .st-kc, .st-kd, .st-ke, .st-kf, .st-kg, .st-kh, .st-ki, .st-kj, .st-kk, .st-kl, .st-km, .st-kn, .st-ko, .st-kp, .st-kq, .st-kr, .st-ks, .st-kt, .st-ku, .st-kv, .st-kw, .st-kx, .st-ky, .st-kz, .st-l0, .st-l1, .st-l2, .st-l3, .st-l4, .st-l5, .st-l6, .st-l7, .st-l8, .st-l9, .st-la, .st-lb, .st-lc, .st-ld, .st-le, .st-lf, .st-lg, .st-lh, .st-li, .st-lj, .st-lk, .st-ll, .st-lm, .st-ln, .st-lo, .st-lp, .st-lq, .st-lr, .st-ls, .st-lt, .st-lu, .st-lv, .st-lw, .st-lx, .st-ly, .st-lz, .st-m0, .st-m1, .st-m2, .st-m3, .st-m4, .st-m5, .st-m6, .st-m7, .st-m8, .st-m9, .st-ma, .st-mb, .st-mc, .st-md, .st-me, .st-mf, .st-mg, .st-mh, .st-mi, .st-mj, .st-mk, .st-ml, .st-mm, .st-mn, .st-mo, .st-mp, .st-mq, .st-mr, .st-ms, .st-mt, .st-mu, .st-mv, .st-mw, .st-mx, .st-my, .st-mz, .st-n0, .st-n1, .st-n2, .st-n3, .st-n4, .st-n5, .st-n6, .st-n7, .st-n8, .st-n9, .st-na, .st-nb, .st-nc, .st-nd, .st-ne, .st-nf, .st-ng, .st-nh, .st-ni, .st-nj, .st-nk, .st-nl, .st-nm, .st-nn, .st-no, .st-np, .st-nq, .st-nr, .st-ns, .st-nt, .st-nu, .st-nv, .st-nw, .st-nx, .st-ny, .st-nz, .st-o0, .st-o1, .st-o2, .st-o3, .st-o4, .st-o5, .st-o6, .st-o7, .st-o8, .st-o9, .st-oa, .st-ob, .st-oc, .st-od, .st-oe, .st-of, .st-og, .st-oh, .st-oi, .st-oj, .st-ok, .st-ol, .st-om, .st-on, .st-oo, .st-op, .st-oq, .st-or, .st-os, .st-ot, .st-ou, .st-ov, .st-ow, .st-ox, .st-oy, .st-oz, .st-p0, .st-p1, .st-p2, .st-p3, .st-p4, .st-p5, .st-p6, .st-p7, .st-p8, .st-p9, .st-pa, .st-pb, .st-pc, .st-pd, .st-pe, .st-pf, .st-pg, .st-ph, .st-pi, .st-pj, .st-pk, .st-pl, .st-pm, .st-pn, .st-po, .st-pp, .st-pq, .st-pr, .st-ps, .st-pt, .st-pu, .st-pv, .st-pw, .st-px, .st-py, .st-pz, .st-q0, .st-q1, .st-q2, .st-q3, .st-q4, .st-q5, .st-q6, .st-q7, .st-q8, .st-q9, .st-qa, .st-qb, .st-qc, .st-qd, .st-qe, .st-qf, .st-qg, .st-qh, .st-qi, .st-qj, .st-qk, .st-ql, .st-qm, .st-qn, .st-qo, .st-qp, .st-qq, .st-qr, .st-qs, .st-qt, .st-qu, .st-qv, .st-qw, .st-qx, .st-qy, .st-qz, .st-r0, .st-r1, .st-r2, .st-r3, .st-r4, .st-r5, .st-r6, .st-r7, .st-r8, .st-r9, .st-ra, .st-rb, .st-rc, .st-rd, .st-re, .st-rf, .st-rg, .st-rh, .st-ri, .st-rj, .st-rk, .st-rl, .st-rm, .st-rn, .st-ro, .st-rp, .st-rq, .st-rr, .st-rs, .st-rt, .st-ru, .st-rv, .st-rw, .st-rx, .st-ry, .st-rz, .st-s0, .st-s1, .st-s2, .st-s3, .st-s4, .st-s5, .st-s6, .st-s7, .st-s8, .st-s9, .st-sa, .st-sb, .st-sc, .st-sd, .st-se, .st-sf, .st-sg, .st-sh, .st-si, .st-sj, .st-sk, .st-sl, .st-sm, .st-sn, .st-so, .st-sp, .st-sq, .st-sr, .st-ss, .st-st, .st-su, .st-sv, .st-sw, .st-sx, .st-sy, .st-sz, .st-t0, .st-t1, .st-t2, .st-t3, .st-t4, .st-t5, .st-t6, .st-t7, .st-t8, .st-t9, .st-ta, .st-tb, .st-tc, .st-td, .st-te, .st-tf, .st-tg, .st-th, .st-ti, .st-tj, .st-tk, .st-tl, .st-tm, .st-tn, .st-to, .st-tp, .st-tq, .st-tr, .st-ts, .st-tt, .st-tu, .st-tv, .st-tw, .st-tx, .st-ty, .st-tz, .st-u0, .st-u1, .st-u2, .st-u3, .st-u4, .st-u5, .st-u6, .st-u7, .st-u8, .st-u9, .st-ua, .st-ub, .st-uc, .st-ud, .st-ue, .st-uf, .st-ug, .st-uh, .st-ui, .st-uj, .st-uk, .st-ul, .st-um, .st-un, .st-uo, .st-up, .st-uq, .st-ur, .st-us, .st-ut, .st-uu, .st-uv, .st-uw, .st-ux, .st-uy, .st-uz, .st-v0, .st-v1, .st-v2, .st-v3, .st-v4, .st-v5, .st-v6, .st-v7, .st-v8, .st-v9, .st-va, .st-vb, .st-vc, .st-vd, .st-ve, .st-vf, .st-vg, .st-vh, .st-vi, .st-vj, .st-vk, .st-vl, .st-vm, .st-vn, .st-vo, .st-vp, .st-vq, .st-vr, .st-vs, .st-vt, .st-vu, .st-vv, .st-vw, .st-vx, .st-vy, .st-vz, .st-w0, .st-w1, .st-w2, .st-w3, .st-w4, .st-w5, .st-w6, .st-w7, .st-w8, .st-w9, .st-wa, .st-wb, .st-wc, .st-wd, .st-we, .st-wf, .st-wg, .st-wh, .st-wi, .st-wj, .st-wk, .st-wl, .st-wm, .st-wn, .st-wo, .st-wp, .st-wq, .st-wr, .st-ws, .st-wt, .st-wu, .st-wv, .st-ww, .st-wx, .st-wy, .st-wz, .st-x0, .st-x1, .st-x2, .st-x3, .st-x4, .st-x5, .st-x6, .st-x7, .st-x8, .st-x9, .st-xa, .st-xb, .st-xc, .st-xd, .st-xe, .st-xf, .st-xg, .st-xh, .st-xi, .st-xj, .st-xk, .st-xl, .st-xm, .st-xn, .st-xo, .st-xp, .st-xq, .st-xr, .st-xs, .st-xt, .st-xu, .st-xv, .st-xw, .st-xx, .st-xy, .st-xz, .st-y0, .st-y1, .st-y2, .st-y3, .st-y4, .st-y5, .st-y6, .st-y7, .st-y8, .st-y9, .st-ya, .st-yb, .st-yc, .st-yd, .st-ye, .st-yf, .st-yg, .st-yh, .st-yi, .st-yj, .st-yk, .st-yl, .st-ym, .st-yn, .st-yo, .st-yp, .st-yq, .st-yr, .st-ys, .st-yt, .st-yu, .st-yv, .st-yw, .st-yx, .st-yy, .st-yz, .st-z0, .st-z1, .st-z2, .st-z3, .st-z4, .st-z5, .st-z6, .st-z7, .st-z8, .st-z9, .st-za, .st-zb, .st-zc, .st-zd, .st-ze, .st-zf, .st-zg, .st-zh, .st-zi, .st-zj, .st-zk, .st-zl, .st-zm, .st-zn, .st-zo, .st-zp, .st-zq, .st-zr, .st-zs, .st-zt, .st-zu, .st-zv, .st-zw, .st-zx, .st-zy, .st-zz { background-color: #222 !important; color: #eee !important; }
            </style>
        """, unsafe_allow_html=True)

    # Navegación rápida entre vistas principales
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Navegación rápida")
    nav_option = st.sidebar.radio(
        "Ir a sección:",
        ["Dashboard", "Buscador de Centros", "Creador de Formularios", "Gestión de Áreas", "Gestión de Usuarios", "Revisión de Envíos"],
        key="nav_selector"
    )
    # Guardar la opción seleccionada en session_state para usar en las tabs
    st.session_state["nav_selected"] = nav_option

    # Cargar los datos del CSV (solo lectura)
    @st.cache_data
    def load_csv_data(file_path):
        """Carga el archivo CSV de centros educativos con manejo de errores y codificaciones."""
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return pd.read_csv(file_path, encoding='latin-1')
            except Exception as e:
                st.error(f"Error al leer el CSV con codificaciones alternativas: {e}")
                st.info("Verifica que el archivo no esté corrupto.")
                return pd.DataFrame()
        except FileNotFoundError:
            st.error(f"Error: No se encontró el archivo {file_path}")
            st.info("Asegúrate de que 'datos_centros.csv' esté en la carpeta principal del proyecto.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error inesperado al leer el CSV: {e}")
            st.info("Verifica que el archivo no esté corrupto.")
            return pd.DataFrame()

    with st.spinner("Cargando datos de centros educativos..."):
        df_centros = load_csv_data("datos_centros.csv")

    # Si el DataFrame está vacío después de intentar cargarlo, detenemos la app.
    if df_centros.empty:
        st.warning("No se pudieron cargar los datos de los centros educativos. La app no puede continuar.")
        st.stop()

    # --- ENRUTADOR POR ROL ---
    # Muestra la interfaz correspondiente al rol del usuario
    if st.session_state["role"] == "admin":
        if admin_view:
            admin_view.show_ui(df_centros)
    elif st.session_state["role"] == "operador":
        if operator_view:
            operator_view.show_ui(df_centros)

# --- PUNTO DE ENTRADA PRINCIPAL ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_screen()