import json
import random

from django.shortcuts import render, redirect
from django.http import Http404
from django.views import View
from hypernews.settings import NEWS_JSON_PATH, MAX_NEWS_ID
from collections import defaultdict
from datetime import datetime


def read_json(path: str) -> list[dict]:
    with open(path, 'r') as f:
        return json.load(f)


def write_json(path: str, obj):
    with open(path, 'w') as f:
        return json.dump(obj, f)


def read_news() -> list[dict]:
    return read_json(NEWS_JSON_PATH)


def write_news(obj: list[dict]):
    write_json(NEWS_JSON_PATH, obj)


def add_news(news: dict):
    all_news = read_news()
    all_news.append(news)
    write_news(all_news)


def get_link() -> int:
    used_links = [int(news['link']) for news in read_news()]
    while True:
        rand = random.randint(0, MAX_NEWS_ID)
        if rand not in used_links:
            return rand


def create_news(title: str, text: str):
    return {'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'text': text,
            'title': title,
            'link': get_link()}


def find_news(link: int) -> dict:
    all_news = read_news()
    for news in all_news:
        if news['link'] == link:
            return news

    raise IndexError


def group_by_date(all_news: list[dict]) -> dict:
    dates_news = defaultdict(list)
    for news in all_news:
        news_datetime: datetime = datetime.strptime(news['created'], '%Y-%m-%d %H:%M:%S')

        dates_news[news_datetime.date()].append(news)
    return {key.strftime('%Y-%m-%d'): value for key, value in sorted(dates_news.items(), key=lambda item: item[0], reverse=True)}


class IndexView(View):
    def get(self, request, *args, **kwargs):
        return redirect('/news/')


class NewsView(View):
    def get(self, request, *args, **kwargs):
        all_news = read_news()
        query = request.GET.get('q', None)

        if query is not None:
            all_news = list(filter(lambda news: query in news['title'].lower(), all_news))

        context = {'all_news': group_by_date(all_news)}
        return render(request, 'news/news.html', context)


class ReadNewsView(View):
    def get(self, request, link, *args, **kwargs):
        try:
            news_link = int(link)
            news_context = find_news(news_link)
        except (ValueError, IndexError):
            raise Http404

        context = news_context
        return render(request, 'news/read_news.html', context)


class CreateView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'news/create_news.html')

    def post(self, request, *args, **kwargs):
        news_info = request.POST
        news_title: str = news_info.get('title')
        news_text: str = news_info.get('text')

        if len(news_title) > 0 and len(news_text) > 0:
            news = create_news(news_title, news_text)
            add_news(news)

        return redirect('/news/')
