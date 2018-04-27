setup: .venv

.venv: requirements.txt
	@virtualenv -p python3.6 $@
	$@/bin/pip install -r $<
	ln -sf $@/bin/activate

clean:
	@rm -rf .venv

.PHONY: setup clean 
