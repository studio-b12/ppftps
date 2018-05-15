dist: setup.py
	.venv/bin/python setup.py sdist bdist_wheel

setup: .venv

.venv: requirements.txt
	@virtualenv -p python3.6 $@
	$@/bin/pip install -r $<
	ln -sf $@/bin/activate

lint:
	@.venv/bin/pylint --rcfile=./.pylintrc ppftps

release: dist
	.venv/bin/twine upload --skip-existing dist/*

clean:
	@rm -rf .venv

.PHONY: setup clean lint release
