"""Tests for B17 forum topic parser."""

from main import Topic, format_telegram_message, parse_topics

SAMPLE_HTML = """
<table>
<tr class="list " id="topic_635381">
<td class="i"><span class="ico_svg ico_svg_18 ico_svg_f2"><span></span></span></td>
<td class="t"><a href="/forum/topic.php?id=635381">Я в тупике</a>
<div class="fio">Автор: Гена #1345753 &nbsp;(Консультирует: Анжела Гульник)</div></td>
<td class="n"><span title="Просмотров: 608">107</span></td>
</tr>
<tr class="list " id="topic_635567">
<td class="i"><span class="ico_svg ico_svg_18 ico_svg_f1"><span></span></span></td>
<td class="t"><a href="/forum/topic.php?id=635567">Ужасно дискомфортно</a>
<div class="fio">Автор: kussya</div></td>
<td class="n"><span title="Просмотров: 339">0</span></td>
</tr>
<tr class="list " id="topic_635999">
<td class="i"><span class="ico_svg ico_svg_18 ico_svg_f2"><span></span></span></td>
<td class="t"><a href="/forum/topic.php?id=635999">Новая тема</a>
<div class="fio">Автор: Тест</div></td>
<td class="n"><span title="Просмотров: 12">0</span></td>
</tr>
<tr class="list " id="topic_636000">
<td class="i"><span class="ico_svg ico_svg_18 ico_svg_f2"><span></span></span></td>
<td class="t"><a href="/forum/topic.php?id=636000">Уже с консультантом</a>
<div class="fio">Автор: Кто-то (Консультирует: Иван Иванов)</div></td>
<td class="n"><span title="Просмотров: 5">0</span></td>
</tr>
</table>
"""


def test_parse_topics_f2_without_consultant_and_zero_replies():
    topics = parse_topics(SAMPLE_HTML)
    assert len(topics) == 1
    topic = topics[0]
    assert topic.topic_id == "635999"
    assert topic.title == "Новая тема"
    assert topic.url == "https://www.b17.ru/forum/topic.php?id=635999"
    assert topic.author_line == "Автор: Тест"


def test_ignores_f2_with_replies():
    topics = parse_topics(SAMPLE_HTML)
    assert all(topic.topic_id != "635381" for topic in topics)


def test_ignores_f1_with_zero_replies():
    topics = parse_topics(SAMPLE_HTML)
    assert all(topic.topic_id != "635567" for topic in topics)


def test_ignores_f2_with_consultant_assigned():
    topics = parse_topics(SAMPLE_HTML)
    assert all(topic.topic_id != "636000" for topic in topics)


def test_telegram_message_contains_clickable_link():
    topic = Topic(
        topic_id="635999",
        title="Новая тема",
        url="https://www.b17.ru/forum/topic.php?id=635999",
        author_line="Автор: Тест",
    )
    message = format_telegram_message(topic)
    assert '<a href="https://www.b17.ru/forum/topic.php?id=635999">' in message
    assert "Открыть тему на B17.ru</a>" in message
    assert "Консультирует" not in message
