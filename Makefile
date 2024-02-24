build:
	pip install -r requirements.txt

clean:
	rm -rf `find . -name __pycache__`
	rm -rf `find . -name instance`
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
