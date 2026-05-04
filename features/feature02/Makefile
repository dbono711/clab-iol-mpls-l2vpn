FEATURE_DIR := .
PYATS_TESTBED := tests/testbed.yaml
PYATS_JOB := tests/job.py
LAB_MGMT_IPS := 10.0.0.2 10.0.0.3 10.0.0.4

include ../../automation/feature.mk

.PHONY: refresh-known-hosts validate

refresh-known-hosts:
	@$(call log,Refreshing SSH known_hosts entries for lab management IPs...)
	@for ip in $(LAB_MGMT_IPS); do \
		ssh-keygen -f "$(HOME)/.ssh/known_hosts" -R "$$ip" >/dev/null 2>&1 || true; \
	done

validate: initialize-virtual-environment refresh-known-hosts
	@$(call log,Running pyATS validation for Feature 02...)
	@PATH=$(VENV_DIR)/bin:$(PATH) ANSIBLE_CONFIG=$(REPO_ROOT)/automation/ansible.cfg \
	$(VENV_DIR)/bin/pyats run job $(PYATS_JOB) \
		--testbed-file $(PYATS_TESTBED) | tee -a $(LOG_FILE)
