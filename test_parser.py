"""Tests for B17 forum topic parser."""

from main import parse_topics

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
<div class="fio">Автор: Тест (Консультирует: Иван Иванов)</div></td>
<td class="n"><span title="Просмотров: 12">0</span></td>
</tr>
</table>
"""


def test_parse_topics_f2_with_zero_replies_only():
    topics = parse_topics(SAMPLE_HTML)
    assert len(topics) == 1
    topic = topics[0]
    assert topic.topic_id == "635999"
    assert topic.title == "Новая тема"
    assert topic.url == "https://www.b17.ru/forum/topic.php?id=635999"
    assert "Тест" in topic.author_line
    assert topic.consultant == "Иван Иванов"


def test_ignores_f2_with_replies():
    topics = parse_topics(SAMPLE_HTML)
    assert all(topic.topic_id != "635381" for topic in topics)


def test_ignores_f1_with_zero_replies():
    topics = parse_topics(SAMPLE_HTML)
    assert all(topic.topic_id != "635567" for topic in topics)
