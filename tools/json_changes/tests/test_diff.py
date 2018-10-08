from tools.json_changes.__main__ import calculate_diff


def test_diff__no_changes():
    current = ['OMG']
    new = ['OMG']

    diff = calculate_diff(current, new)

    assert not diff.removed
    assert not diff.added


def test_diff__knc_added():
    current = ['OMG']
    new = ['OMG', 'KNC']

    diff = calculate_diff(current, new)

    assert not diff.removed
    assert set(diff.added) == {'KNC'}


def test_diff__omg_removed():
    current = ['OMG', 'KNC']
    new = ['KNC']

    diff = calculate_diff(current, new)

    assert set(diff.removed) == {'OMG'}
    assert not diff.added


def test_diff__knc_added_omg_removed():
    current = ['OMG']
    new = ['KNC']

    diff = calculate_diff(current, new)

    assert set(diff.removed) == {'OMG'}
    assert set(diff.added) == {'KNC'}
