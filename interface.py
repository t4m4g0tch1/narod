from dash import Dash, dcc, html, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
import zipfile
import ast
import os

# Загрузка данных из файла
df = pd.read_csv('csv/websites_100.csv', index_col=0)

# Обработка данных
df['internal_links_count'] = df['internal_links'].apply(
    lambda x: len(ast.literal_eval(x)) if isinstance(x, str) else 0)
df['internal_links'] = df['internal_links'].astype(str)
df['link_level'] = df['internal_links'].str.count('/').sub(2).clip(lower=0)

# Преобразование колонок в целочисленный формат
df[['duration', 'main_page_date_begin', 'main_page_date_ending']] = df[['duration', 'main_page_date_begin',
                                                                        'main_page_date_ending']].apply(pd.to_numeric, errors='coerce').astype(pd.Int32Dtype())

# Создание категорий для уровней вложенности
bins = [0, 5, 10, 100, 500, 1000, float('inf')]
labels = ['0-5', '5-10', '10-100', '100-500', '500-1000', '1000+']
df['link_level_category'] = pd.cut(
    df['link_level'], bins=bins, labels=labels, right=False)

# Выбор 10 случайных строк (для демонстрации датасета)
random_10_sites = df.sample(n=10)

# Выбор топ-10 сайтов по длине текста
top_10_sites = df.nlargest(10, 'main_page_text_len')

# Фильтрация данных
sensitive_content_df = df[df['main_page_warning'] != '0']
sensitive_content_counts = sensitive_content_df['main_page_warning'].value_counts(
).reset_index()
sensitive_content_counts.columns = ['category', 'count']

# Initialize the app
asst_path = os.path.join(os.getcwd(), "screens")

if not os.path.exists(asst_path):
    zip_path = os.path.join(os.getcwd(), 'screens.zip')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.getcwd())

app = Dash(__name__, external_stylesheets=[
           dbc.themes.BOOTSTRAP], assets_folder=asst_path)
app.config.suppress_callback_exceptions = True

# Макет главного дашборда


main_dashboard = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(html.H1("Narod.ru", style={
                'textAlign': 'center', 'color': 'cyan'}), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("Warning-контент"),
                dcc.Dropdown(
                    id='stat-dropdown-main_page_warning',
                    options=[{'label': str(main_page_warning), 'value': main_page_warning}
                             for main_page_warning in sorted(df['main_page_warning'].unique())],
                    placeholder="Выберите категорию",
                    multi=True
                ),
                html.Label("Язык сайта"),
                dcc.Dropdown(
                    id='stat-dropdown-language',
                    options=[{'label': str(language), 'value': language} for language in sorted(
                        df['main_page_language_name'].unique())],
                    placeholder="Выберите язык",
                    multi=True
                ),
                html.Label("Предполагаемая дата создания сайта"),
                dcc.Dropdown(
                    id='stat-dropdown-date-begin',
                    options=[{'label': str(main_page_date_begin), 'value': main_page_date_begin}
                             for main_page_date_begin in sorted(df['main_page_date_begin'].dropna().unique())],
                    placeholder="Выберите год",
                    multi=True
                ),
                html.Label("Предполагаемая дата последней модификации сайта"),
                dcc.Dropdown(
                    id='stat-dropdown-date-ending',
                    options=[{'label': str(main_page_date_ending), 'value': main_page_date_ending}
                             for main_page_date_ending in sorted(df['main_page_date_ending'].dropna().unique())],
                    placeholder="Выберите год",
                    multi=True
                ),
                html.Label(
                    "Предполагаемая продолжительность активности сайта"),
                dcc.Dropdown(
                    id='stat-dropdown-duration',
                    options=[{'label': str(duration), 'value': duration} for duration in sorted(
                        df['duration'].dropna().unique())],
                    placeholder="Выберите диапазон",
                    multi=True
                )
            ], style={'padding': '20px'})
        ], width=3, style={'position': 'sticky', 'top': 0, 'height': '100vh', 'overflow-y': 'auto'}),
        dbc.Col([
            html.Div([
                html.Div(children=dcc.Graph(id='histo-chart-final'), style={
                         'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-right': '10px'}),
                html.Div(children=dcc.Graph(id='duration-histo-chart'), style={
                         'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-top': '20px'})
            ], style={'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
            html.Div([
                html.Div(children=dcc.Graph(id='treemap-chart'), style={
                         'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-top': '20px'}),
                html.Div(children=dcc.Graph(id='tree-chart-final'), style={
                         'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-top': '20px'})
            ], style={'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
            dbc.Row([
                dbc.Col(html.Div(children=dcc.Graph(
                    id='pie-chart-final')), width=6),
                dbc.Col(html.Div(children=dcc.Graph(
                    id='sensitive-content-chart')), width=6)
            ])
        ], width=9)
    ])
], style={'display': 'block'}, id='main-dashboard')


# Макет таблицы
dataset_table = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='dropdown-main_page_warning',
            options=[{'label': str(main_page_warning), 'value': main_page_warning}
                     for main_page_warning in sorted(df['main_page_warning'].unique())],
            placeholder="Выберите категорию main_page_Warning",
            multi=True
        ), width=6),
        dbc.Col(dcc.Dropdown(
            id='dropdown-language',
            options=[{'label': str(language), 'value': language} for language in sorted(
                df['main_page_language_name'].unique())],
            placeholder="Выберите язык сайта",
            multi=True
        ), width=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='dropdown-date-begin',
            options=[{'label': str(main_page_date_begin), 'value': main_page_date_begin}
                     for main_page_date_begin in sorted(df['main_page_date_begin'].dropna().unique())],
            placeholder="Предполагаемый год создания",
            multi=True
        ), width=4),
        dbc.Col(dcc.Dropdown(
            id='dropdown-date-ending',
            options=[{'label': str(main_page_date_ending), 'value': main_page_date_ending}
                     for main_page_date_ending in sorted(df['main_page_date_ending'].dropna().unique())],
            placeholder="Предполагаемый год последней модификации",
            multi=True
        ), width=4),
        dbc.Col(dcc.Dropdown(
            id='dropdown-duration',
            options=[{'label': str(duration), 'value': duration}
                     for duration in sorted(df['duration'].dropna().unique())],
            placeholder="Продолжительность активности",
            multi=True
        ), width=4)
    ]),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                data=random_10_sites.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'minWidth': '100px',
                            'width': '100px', 'maxWidth': '100px'},
                id='table',
                sort_action='native'
            )
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='dropdown-columns',
            options=[{'label': col, 'value': col} for col in df.columns],
            multi=True,
            value=df.columns.tolist(),
            placeholder="Выберите столбцы"
        ), width=12)
    ])
])

# Макет страницы с информацией о сайте
site_info = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='domain-dropdown',
            options=[{'label': domain, 'value': domain}
                for domain in df['domain'].unique()],
            placeholder="Выберите домен",
            value=None
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='dashboard'), width=12)
    ])
])

# Объединенный макет приложения с вкладками
app.layout = dbc.Container(fluid=True, children=[
    dcc.Tabs(id='tabs-example', value='tab-1', children=[
        dcc.Tab(label='Статистика', value='tab-1'),
        dcc.Tab(label='Датасет', value='tab-2'),
        dcc.Tab(label='Сайты', value='tab-3'),
    ]),
    html.Div(id='tabs-content-example')
])

# Callback для переключения вкладок


@app.callback(
    Output('tabs-content-example', 'children'),
    Input('tabs-example', 'value')
)
def render_content(tab):
    if tab == 'tab-1':
        return main_dashboard
    elif tab == 'tab-2':
        return dataset_table
    elif tab == 'tab-3':
        return site_info

# Callback для обновления графиков


@app.callback(
    [Output('histo-chart-final', 'figure'),
     Output('duration-histo-chart', 'figure'),
     Output('treemap-chart', 'figure'),
     Output('tree-chart-final', 'figure'),
     Output('pie-chart-final', 'figure'),
     Output('sensitive-content-chart', 'figure')],
    [Input('stat-dropdown-main_page_warning', 'value'),
     Input('stat-dropdown-language', 'value'),
     Input('stat-dropdown-date-begin', 'value'),
     Input('stat-dropdown-date-ending', 'value'),
     Input('stat-dropdown-duration', 'value')]
)
def update_charts(selected_main_page_warnings, selected_languages, selected_main_page_date_begin, selected_main_page_date_ending, selected_duration):
    filtered_df = df.copy()
    if selected_main_page_warnings:
        filtered_df = filtered_df[filtered_df['main_page_warning'].isin(
            selected_main_page_warnings)]
    if selected_languages:
        filtered_df = filtered_df[filtered_df['main_page_language_name'].isin(
            selected_languages)]
    if selected_main_page_date_begin:
        filtered_df = filtered_df[filtered_df['main_page_date_begin'].isin(
            selected_main_page_date_begin)]
    if selected_main_page_date_ending:
        filtered_df = filtered_df[filtered_df['main_page_date_ending'].isin(
            selected_main_page_date_ending)]
    if selected_duration:
        filtered_df = filtered_df[filtered_df['duration'].isin(
            selected_duration)]
    histo_chart = create_histo_chart(filtered_df)
    duration_histogram = create_duration_histogram(filtered_df)
    treemap_chart = create_treemap(filtered_df)
    tree_chart = create_tree_chart(filtered_df)
    pie_chart = create_pie_chart(filtered_df)
    sensitive_content_chart = create_sensitive_content_chart(filtered_df)
    return histo_chart, duration_histogram, treemap_chart, tree_chart, pie_chart, sensitive_content_chart

# Callback для обновления таблицы на основе выбранных фильтров и столбцов


@app.callback(
    [Output('table', 'data'), Output('table', 'columns')],
    [Input('dropdown-main_page_warning', 'value'), Input('dropdown-language', 'value'), Input('dropdown-date-begin', 'value'),
     Input('dropdown-date-ending', 'value'), Input('dropdown-duration', 'value'), Input('dropdown-columns', 'value')]
)
def update_table(selected_main_page_warnings, selected_languages, selected_main_page_date_begin, selected_main_page_date_ending, selected_duration, selected_columns):
    filtered_df = df.copy()

    if selected_main_page_warnings:
        filtered_df = filtered_df[filtered_df['main_page_warning'].isin(
            selected_main_page_warnings)]

    if selected_languages:
        filtered_df = filtered_df[filtered_df['main_page_language_name'].isin(
            selected_languages)]

    if selected_main_page_date_begin:
        filtered_df = filtered_df[filtered_df['main_page_date_begin'].isin(
            selected_main_page_date_begin)]

    if selected_main_page_date_ending:
        filtered_df = filtered_df[filtered_df['main_page_date_ending'].isin(
            selected_main_page_date_ending)]

    if selected_duration:
        filtered_df = filtered_df[filtered_df['duration'].isin(
            selected_duration)]

    # Выбираем 10 строк или все строки, если их меньше 10
    num_rows = min(10, len(filtered_df))
    filtered_df = filtered_df.sample(n=num_rows)

    data = filtered_df[selected_columns].to_dict('records')
    columns = [{"name": i, "id": i} for i in selected_columns]

    return data, columns

# Callback для обновления информации о выбранном сайте


@app.callback(
    Output('dashboard', 'children'),
    Input('domain-dropdown', 'value')
)
def update_dashboard(selected_domain):
    if not selected_domain:
        return []

    site_data = df[df['domain'] == selected_domain].iloc[0]

    # Превью изображения
    image_fimain_page_text_ame = site_data.preview_file_name if 'preview_file_name' in df.columns else None
    if image_fimain_page_text_ame and os.path.exists(os.path.join(asst_path, image_fimain_page_text_ame)):
        image_src = app.get_asset_url(image_fimain_page_text_ame)
    else:
        image_src = 'https://via.placeholder.com/450'  # URL заглушки

    preview_image = html.Img(src=image_src, style={
                             'maxWidth': '100%', 'height': 'auto', 'margin-top': '10px'})

    # Информация о сенситивном контенте
    sensitive_content = html.P(f"Сенситивный контент: {'Да' if site_data['main_page_warning'] != '0' else 'Нет'}" + (
        f" (категория: {site_data['main_page_warning']})" if site_data['main_page_warning'] != '0' else ""))

    # Информация о языке и внутренних ссылках
    language_info = html.P(
        f"Язык: {'N/A' if site_data['main_page_language_name'] == 'Unknown (0%)' else site_data['main_page_language_name']}"
    )
    internal_links_info = html.P(f"Количество внутренних ссылок: {site_data['internal_links_count']}")

    # Упоминаемые даты
    mentioned_dates = site_data['main_page_numbers']
    mentioned_dates_str = ', '.join(map(str, ast.literal_eval(
        mentioned_dates))) if mentioned_dates and mentioned_dates != '[]' else 'Нет'
    mentioned_dates_info = html.P(f"Упоминаемые даты: {mentioned_dates_str}")

    dashboard_content = [
        html.H2(html.A(f"Сайт: https://{selected_domain}.narod.ru/", href=f"https://{selected_domain}.narod.ru/", target="_blank", style={'color': '#05fc26'}), style={'margin-bottom': '15px'}),
        html.Div([
            html.Div(preview_image, style={
                     'flex': '0 0 70%', 'maxWidth': '70%', 'vertical-align': 'top'}),
            html.Div([
                sensitive_content,
                language_info,
                internal_links_info,
                mentioned_dates_info
            ], style={'flex': '1', 'padding-left': '20px', 'vertical-align': 'top'})
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'gap': '20px'})
    ]

    return dashboard_content

# Функции для создания графиков


def create_histo_chart(filtered_df):
    fig = px.bar(
        filtered_df.nlargest(10, 'main_page_text_len'), x='domain', y='main_page_text_len', color='domain', color_continuous_scale='Viridis')
    fig.update_layout(
        title_text='Топ-10 сайтов по объему текста',
        title_x=0.5,
        title_y=0.9,
        margin=dict(t=75),
        xaxis_title="Сайт",
        yaxis_title="Длина текста (знаки)",
        showlegend=False,

    )
    fig.update_yaxes(tickformat=' ')
    # fig.update_traces(hoverinfo="all", hovertemplate="<b>Длина текста: %{customdata[1]}</b>")
    return fig


def create_duration_histogram(filtered_df):
    fig = px.histogram(filtered_df, x='duration',
                       title='Предполагаемый срок активности сайта')
    fig.update_layout(
        title_x=0.5,
        title_y=0.95,
        margin=dict(t=50),
        xaxis_title="Срок активности (годы)",
        yaxis_title="Количество сайтов"
    )
    # fig.update_traces(hoverinfo="all", hovertemplate="<b>Количество: %{count]}<br>Cрок активности: %{customdata[1]}</b>")
    return fig


def create_treemap(filtered_df):
    fig = px.treemap(filtered_df,
                     path=['domain'],
                     values='internal_links_count',
                     title='Количество внутренних ссылок',
                     custom_data=['domain', 'internal_links_count']
                     )
    fig.update_layout(title_x=0.5,
                      title_y=0.95,
                      width=550,
                      height=550,
                      margin=dict(t=40)
                      )
    fig.update_traces(hoverinfo="all",
                      hovertemplate="<b>Количество ссылок: %{customdata[1]}</b>")
    return fig


def create_tree_chart(filtered_df):
    fig = px.treemap(filtered_df,
                     path=['link_level_category', 'internal_links'],
                     color='link_level_category',
                     title='Уровень вложенности внутренних ссылок',
                     custom_data=['domain']
                     )

    fig.update_layout(title_text='Уровень вложенности внутренних ссылок',
                      title_x=0.5,
                      title_y=0.95,
                      width=550,
                      height=550,
                      margin=dict(t=40))

    fig.update_traces(hoverinfo="all",
                      hovertemplate="<b>Домен: %{customdata[0]}</b>")
    return fig


def create_pie_chart(filtered_df):
    total_domains = filtered_df['domain'].nunique()
    domains_with_main_page_warnings = filtered_df[filtered_df['main_page_warning'] != '0']['domain'].nunique(
    )
    data = {'Domains': ['Нет контента 18+', 'Контент 18+'],
            'Count': [total_domains - domains_with_main_page_warnings, domains_with_main_page_warnings]}

    fig = px.pie(pd.DataFrame(data),
                 values='Count',
                 names='Domains',
                 title='Сайты, содержащие сенситивный контент',
                 color_discrete_sequence=['#636EFA', '#EF553B']
                 )

    fig.update_traces(textinfo='percent',
                      textposition='inside',
                      textfont_size=12,
                      insidetextorientation='radial')

    fig.update_layout(title_x=0.5,
                      title_y=0.95)
    return fig


def create_sensitive_content_chart(filtered_df):
    legend_dict = {'porn': 'порно',
                   'drugs': 'наркотики',
                   'suicide': 'суицид',
                   'race_discr': 'рассов.дискр.',
                   'bad_words': 'ругательства'}

    sensitive_content_counts = filtered_df[filtered_df['main_page_warning']
                                           != '0']['main_page_warning'].value_counts().reset_index()
    sensitive_content_counts.columns = ['category', 'count']

    # Заменяем наименования в легенде согласно словарю
    sensitive_content_counts['category'] = sensitive_content_counts['category'].map(
        legend_dict)

    fig = px.pie(sensitive_content_counts,
                 values='count',
                 names='category',
                 title='Сенситивный контент по категориям',
                 hole=0.5
                 )
    fig.update_traces(textinfo='percent', textposition='inside',
                      textfont_size=12, insidetextorientation='radial')
    fig.update_layout(title_x=0.5, title_y=0.95)
    return fig


# Запуск приложения
if __name__ == '__main__':
    app.run_server(debug=True, port=8059)
