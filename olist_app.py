import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ─────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Olist Dashboard",
    page_icon="🛒",
    layout="wide"
)

# ─────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────
@st.cache_data
def cargar_datos():
    customers     = pd.read_csv('data/olist_customers_dataset.csv')
    order_items   = pd.read_csv('data/olist_order_items_dataset.csv')
    payments      = pd.read_csv('data/olist_order_payments_dataset.csv')
    reviews       = pd.read_csv('data/olist_order_reviews_dataset.csv')
    orders        = pd.read_csv('data/olist_orders_dataset.csv')
    products      = pd.read_csv('data/olist_products_dataset.csv')
    sellers       = pd.read_csv('data/olist_sellers_dataset.csv')
    category_tr   = pd.read_csv('data/product_category_name_translation.csv')

    # Filtramos solo pedidos entregados
    orders = orders[orders['order_status'] == 'delivered'].copy()

    # Convertimos fechas
    date_cols = ['order_purchase_timestamp', 'order_approved_at',
                 'order_delivered_carrier_date', 'order_delivered_customer_date',
                 'order_estimated_delivery_date']
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col])

    # Tiempo de entrega
    orders['delivery_days'] = (
        orders['order_delivered_customer_date'] -
        orders['order_purchase_timestamp']
    ).dt.days

    orders['year_month'] = orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
    orders['year']       = orders['order_purchase_timestamp'].dt.year
    orders['month']      = orders['order_purchase_timestamp'].dt.month

    return orders, customers, order_items, payments, reviews, products, sellers, category_tr

orders, customers, order_items, payments, reviews, products, sellers, category_tr = cargar_datos()

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN
# ─────────────────────────────────────────
st.title("🛒 Olist E-Commerce — Dashboard Ejecutivo")
st.markdown("Análisis completo del marketplace brasileño Olist (2016-2018)")
st.divider()

# ─────────────────────────────────────────
# KPIs PRINCIPALES
# ─────────────────────────────────────────
total_pedidos    = len(orders)
ingresos_totales = order_items['price'].sum()
ticket_promedio  = ingresos_totales / total_pedidos
entrega_promedio = orders['delivery_days'].mean()

df_reviews_kpi   = orders[['order_id']].merge(reviews, on='order_id')
score_promedio   = df_reviews_kpi['review_score'].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📦 Total Pedidos",       f"{total_pedidos:,}")
col2.metric("💰 Ingresos Totales",    f"R$ {ingresos_totales:,.0f}")
col3.metric("🧾 Ticket Promedio",     f"R$ {ticket_promedio:,.0f}")
col4.metric("🚚 Entrega Promedio",    f"{entrega_promedio:.1f} días")
col5.metric("⭐ Score Promedio",      f"{score_promedio:.2f} / 5.0")

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 1 — EVOLUCIÓN DE VENTAS
# ─────────────────────────────────────────
st.subheader("📈 Evolución de Ventas")

ventas_por_mes = orders.groupby('year_month').size().reset_index(name='total_pedidos')

fig1 = px.line(
    ventas_por_mes,
    x='year_month',
    y='total_pedidos',
    markers=True,
    title='Pedidos por Mes',
    labels={'year_month': 'Mes', 'total_pedidos': 'Total Pedidos'}
)
fig1.update_traces(line_color='#2196F3', line_width=2.5)
fig1.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 2 — CATEGORÍAS
# ─────────────────────────────────────────
st.subheader("🏷️ Análisis de Categorías")

df_cat = orders[['order_id']].merge(order_items, on='order_id')
df_cat = df_cat.merge(products[['product_id', 'product_category_name']], on='product_id')
df_cat = df_cat.merge(category_tr, on='product_category_name', how='left')
df_cat['categoria'] = df_cat['product_category_name_english'].fillna(df_cat['product_category_name'])

col_a, col_b = st.columns(2)

with col_a:
    top_vol = (df_cat.groupby('categoria').size()
                     .reset_index(name='total_pedidos')
                     .sort_values('total_pedidos', ascending=False)
                     .head(15))
    fig2 = px.bar(top_vol, x='total_pedidos', y='categoria',
                  orientation='h', title='Top 15 por Volumen',
                  labels={'total_pedidos': 'Pedidos', 'categoria': ''},
                  color='total_pedidos', color_continuous_scale='Blues')
    fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    top_ing = (df_cat.groupby('categoria')['price'].sum()
                     .reset_index(name='ingresos')
                     .sort_values('ingresos', ascending=False)
                     .head(15))
    fig3 = px.bar(top_ing, x='ingresos', y='categoria',
                  orientation='h', title='Top 15 por Ingresos (BRL)',
                  labels={'ingresos': 'Ingresos (BRL)', 'categoria': ''},
                  color='ingresos', color_continuous_scale='Oranges')
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 3 — SATISFACCIÓN Y ENTREGA
# ─────────────────────────────────────────
st.subheader("⭐ Satisfacción vs Entrega")

df_rev = orders[['order_id', 'delivery_days']].merge(reviews, on='order_id')
entrega_score = df_rev.groupby('review_score')['delivery_days'].mean().round(1).reset_index()

col_c, col_d = st.columns(2)

with col_c:
    score_dist = df_rev['review_score'].value_counts().sort_index().reset_index()
    score_dist.columns = ['score', 'cantidad']
    fig4 = px.bar(score_dist, x='score', y='cantidad',
                  title='Distribución de Puntajes',
                  labels={'score': 'Puntaje', 'cantidad': 'Cantidad'},
                  color='score',
                  color_continuous_scale=['#F44336','#FF9800','#FFC107','#8BC34A','#4CAF50'])
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    fig5 = px.bar(entrega_score, x='review_score', y='delivery_days',
                  title='Días de Entrega por Puntaje',
                  labels={'review_score': 'Puntaje', 'delivery_days': 'Días promedio'},
                  color='delivery_days',
                  color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 4 — GEOGRAFÍA
# ─────────────────────────────────────────
st.subheader("🗺️ Análisis Geográfico")

df_geo = orders[['order_id', 'customer_id']].merge(
    customers[['customer_id', 'customer_state']], on='customer_id'
)
pedidos_estado = (df_geo.groupby('customer_state').size()
                        .reset_index(name='total_pedidos')
                        .sort_values('total_pedidos', ascending=False))

fig6 = px.bar(pedidos_estado, x='customer_state', y='total_pedidos',
              title='Pedidos por Estado',
              labels={'customer_state': 'Estado', 'total_pedidos': 'Total Pedidos'},
              color='total_pedidos', color_continuous_scale='Blues')
st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 5 — SEGMENTACIÓN RFM
# ─────────────────────────────────────────
st.subheader("👥 Segmentación de Clientes (RFM)")

fecha_ref = orders['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
df_rfm = orders[['order_id', 'customer_id', 'order_purchase_timestamp']].merge(
    payments.groupby('order_id')['payment_value'].sum().reset_index(), on='order_id'
)
rfm = df_rfm.groupby('customer_id').agg(
    recencia   = ('order_purchase_timestamp', lambda x: (fecha_ref - x.max()).days),
    frecuencia = ('order_id', 'count'),
    monto      = ('payment_value', 'sum')
).reset_index()

# Nota: no usamos Frecuencia (F) porque en este dataset el 100% de los
# clientes compró una sola vez -> F es constante (siempre 1) y no aporta
# nada para segmentar. Por eso el modelo se reduce a R y M.
rfm['R_score'] = pd.qcut(rfm['recencia'], q=4, labels=[4, 3, 2, 1]).astype(int)
rfm['M_score'] = pd.qcut(rfm['monto'].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int)

def segmentar(row):
    r, m = row['R_score'], row['M_score']
    if r >= 3 and m >= 3:   return 'Campeones'
    elif r >= 3 and m < 3:  return 'Recientes de bajo valor'
    elif r < 3 and m >= 3:  return 'En riesgo — alto valor'
    else:                   return 'Perdidos'

rfm['segmento'] = rfm.apply(segmentar, axis=1)

resumen_rfm = rfm.groupby('segmento').agg(
    total_clientes = ('customer_id', 'count'),
    monto_prom     = ('monto', 'mean'),
    recencia_prom  = ('recencia', 'mean')
).round(1).reset_index()

col_e, col_f = st.columns(2)

with col_e:
    fig7 = px.pie(resumen_rfm, values='total_clientes', names='segmento',
                  title='Distribución de Segmentos',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig7, use_container_width=True)

with col_f:
    fig8 = px.bar(resumen_rfm, x='segmento', y='monto_prom',
                  title='Monto Promedio por Segmento (BRL)',
                  labels={'segmento': 'Segmento', 'monto_prom': 'Monto Promedio (BRL)'},
                  color='segmento',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig8, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# SECCIÓN 6 — PERFORMANCE DE VENDEDORES (CUADRANTES)
# ─────────────────────────────────────────
st.subheader("🏪 Performance de Vendedores por Cuadrantes")

df_sellers = orders[['order_id']].merge(
    order_items[['order_id', 'seller_id', 'price']], on='order_id'
)
df_sellers = df_sellers.merge(reviews[['order_id', 'review_score']], on='order_id', how='left')

seller_metrics = df_sellers.groupby('seller_id').agg(
    total_ventas   = ('order_id', 'count'),
    ingresos       = ('price', 'sum'),
    score_promedio = ('review_score', 'mean')
).round(2).reset_index()

# Solo vendedores con 10+ ventas, para que el score promedio sea representativo
seller_metrics = seller_metrics[seller_metrics['total_ventas'] >= 10].copy()

ingresos_mediana = seller_metrics['ingresos'].median()
score_mediana    = seller_metrics['score_promedio'].median()

def clasificar_vendedor(row):
    alto_ingreso = row['ingresos'] >= ingresos_mediana
    alto_score   = row['score_promedio'] >= score_mediana
    if alto_ingreso and alto_score:
        return 'Estrellas'
    elif alto_ingreso and not alto_score:
        return 'Riesgo reputacional'
    elif not alto_ingreso and alto_score:
        return 'Consistentes'
    else:
        return 'Bajo rendimiento'

seller_metrics['segmento'] = seller_metrics.apply(clasificar_vendedor, axis=1)

col_g, col_h = st.columns([2, 1])

with col_g:
    fig9 = px.scatter(
        seller_metrics, x='ingresos', y='score_promedio',
        color='segmento', size='total_ventas',
        hover_data=['seller_id', 'total_ventas'],
        title=f'Ingresos vs. Satisfacción por vendedor (mín. 10 ventas, n={len(seller_metrics):,})',
        labels={'ingresos': 'Ingresos totales (BRL)', 'score_promedio': 'Score promedio'},
        color_discrete_map={
            'Estrellas': '#4CAF50',
            'Riesgo reputacional': '#F44336',
            'Consistentes': '#2196F3',
            'Bajo rendimiento': '#9E9E9E'
        }
    )
    fig9.add_vline(x=ingresos_mediana, line_dash='dash', line_color='gray')
    fig9.add_hline(y=score_mediana, line_dash='dash', line_color='gray')
    st.plotly_chart(fig9, use_container_width=True)

with col_h:
    st.caption("Distribución por segmento")
    resumen_segmento = (seller_metrics['segmento'].value_counts(normalize=True) * 100).round(1)
    for seg in ['Estrellas', 'Riesgo reputacional', 'Consistentes', 'Bajo rendimiento']:
        st.metric(seg, f"{resumen_segmento.get(seg, 0)}%")

st.divider()
st.caption("Dashboard desarrollado con Python y Streamlit | Datos: Olist Brazilian E-Commerce Dataset")