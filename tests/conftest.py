# tests directory-specific settings - this file is run automatically
# by pytest before any tests are run

import pytest, sys, re
from os.path import abspath, dirname, join
from utils.mem import use_gpu
from fastai.gen_doc.doctest import TestAPIRegistry

# make sure we test against the checked out git version of fastai and
# not the pre-installed version. With 'pip install -e .[dev]' it's not
# needed, but it's better to be safe and ensure the git path comes
# second in sys.path (the first path is the test dir path)
git_repo_path = abspath(dirname(dirname(__file__)))
sys.path.insert(1, git_repo_path)

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")
    parser.addoption("--skipint", action="store_true", default=False, help="skip integration tests")
    parser.addoption("--testapireg", action="store_true", default=False, help="test api registry")

def mark_items_with_keyword(items, marker, keyword):
    for item in items:
        if keyword in item.keywords: item.add_marker(marker)

def pytest_collection_modifyitems(config, items):
    if config.getoption("--skipint"):
        skip_int = pytest.mark.skip(reason="--skipint used to skip integration test")
        mark_items_with_keyword(items, skip_int, "integration")

    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        mark_items_with_keyword(items, skip_slow, "slow")

    if not use_gpu:
        skip_cuda = pytest.mark.skip(reason="CUDA is not available")
        mark_items_with_keyword(items, skip_cuda, "cuda")

# test_this functionality integration
@pytest.fixture(scope="session", autouse=True)
def doctest_collector_start(request):
    individualtests = [s for s in set(sys.argv) if re.match(r'.*test_\w+\.py',s)]
    #individualtests = 0
    if pytest.config.getoption("--testapireg") and not individualtests:
        request.addfinalizer(TestAPIRegistry.registry_save)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    res = outcome.get_result()
    filename, lineno, testname = res.location
    if   res.when == "setup":    TestAPIRegistry.this_tests_flag_on(filename, testname)
    elif res.when == "call":     TestAPIRegistry.tests_failed(res.failed)
    elif res.when == "teardown": TestAPIRegistry.this_tests_flag_check(filename, testname)
