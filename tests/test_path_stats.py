from collections import Counter
from nginx_log_monitor.path_stats import cleanup_counter, unify_path





def test_cleanup_counter():
    c = Counter('lorem ipsum dolor sit amet.')
    assert len(c) == 14
    assert c.most_common(5) == [(' ', 4), ('o', 3), ('m', 3), ('l', 2), ('r', 2)]
    assert set(c.items()) == set(c.most_common(100))
    assert cleanup_counter(c, 100) == c
    c2 = cleanup_counter(c, 5)
    assert len(c2) == 5
    assert set(c2.items()) == set(c.most_common(5))

def test_unify_path():
    assert unify_path('/') == '/'
    assert unify_path('/?foo') == '/'
    assert unify_path('/campaigns/f0d219b67cc3409bbd64bc5d5a5286f9/templates') == '/campaigns/<uuid>/templates'
    assert unify_path('/campaigns/4FC67E9593CA409B9427343099CBE9C7/templates') == '/campaigns/<UUID>/templates'
    assert unify_path('/campaigns/8de2fa22-36eb-4e0f-b9cd-4766d5614a9f/templates') == '/campaigns/<uuid>/templates'
    assert unify_path('/campaigns/D91B577E-8C29-45EF-80BE-1D7D35EFED6D/templates') == '/campaigns/<UUID>/templates'
    assert unify_path('/campaigns/1234/templates') == '/campaigns/<n>/templates'
    assert unify_path('/campaigns/f0d219b67cc3409bbd64bc5d5a5286f9') == '/campaigns/<uuid>'
    assert unify_path('/campaigns/4FC67E9593CA409B9427343099CBE9C7') == '/campaigns/<UUID>'
    assert unify_path('/campaigns/8de2fa22-36eb-4e0f-b9cd-4766d5614a9f') == '/campaigns/<uuid>'
    assert unify_path('/campaigns/D91B577E-8C29-45EF-80BE-1D7D35EFED6D') == '/campaigns/<UUID>'
    assert unify_path('/campaigns/1234') == '/campaigns/<n>'
