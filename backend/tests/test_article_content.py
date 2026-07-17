from providers.news.article_content import is_description_insufficient


def test_short_description_is_insufficient():
    assert is_description_insufficient("Şirket haberi açıkladı") is True


def test_empty_description_is_insufficient():
    assert is_description_insufficient("") is True


def test_truncated_description_is_insufficient():
    long_but_truncated = "Şirket bugün önemli bir gelişme açıkladı ve yatırımcılar olumlu tepki verdi, detaylar için..."
    assert is_description_insufficient(long_but_truncated) is True


def test_complete_sentence_is_sufficient():
    complete = (
        "Şirket bugün Faz 2 klinik çalışmasının birincil son noktalarını karşıladığını açıkladı. "
        "Yönetim, sonuçların beklentilerin üzerinde olduğunu ve önümüzdeki çeyrekte Faz 3 başvurusu "
        "yapılacağını belirtti."
    )
    assert is_description_insufficient(complete) is False
