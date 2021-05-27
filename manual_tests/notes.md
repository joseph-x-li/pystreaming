Performance Stats: http://blog.loopbio.com/video-io-2-jpeg-decoding.html

To run tests:
----
```
p -m pytest tests/ --cov=pystreaming --cov-report=html
open htmlcov/index.html  # open html cov report
rm .coverage*            # remove generated temp files (Not really needed)
rm -rf htmlcov .coverage # remove generated html report
```

To format using black:
----
```
p -m black pystreaming/
```

To lint with flake8:
----
```
p -m flake8 --max-line-length=100 pystreaming/
```