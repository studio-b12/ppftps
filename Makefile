setup: .venv

.venv: requirements.txt
	@virtualenv -p python3.6 $@
	$@/bin/pip install -r $<
	ln -sf $@/bin/activate

lint:
	@pylint --rcfile=./.pylintrc ppftps

clean:
	@rm -rf .venv

.PHONY: setup clean lint
