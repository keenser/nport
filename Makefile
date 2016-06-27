NPORT=nport
VERSION=3.2-4
ARCH=all
NPORT_PKG=$(NPORT)_$(VERSION)_armhf.deb
PYLIB=deb/usr/lib/python3/dist-packages/nport
PYCACHE=nport/__pycache__
BBBIP=192.168.7.2

WRAPPER=wrapper
WRAPPER_VERSION=1.4-1
WRAPPER_PKG=update-wrapper_$(WRAPPER_VERSION)_$(ARCH).deb

ALTROUTE=altroute
ALTROUTE_VERSION=1.1-0
ALTROUTE_PKG=$(ALTROUTE)_$(ALTROUTE_VERSION)_$(ARCH).deb

MODEMWATCHDOG=modemwatchdog
MODEMWATCHDOG_VERSION=1.1-4
MODEMWATCHDOG_PKG=$(MODEMWATCHDOG)_$(MODEMWATCHDOG_VERSION)_$(ARCH).deb

WEBADMIN=webadmin
WEBADMIN_VERSION=1.1-0
WEBADMIN_PKG=$(WEBADMIN)_$(WEBADMIN_VERSION)_$(ARCH).deb

WEBADMIN_I=webadmin.impersonal
WEBADMIN_I_VERSION=1.1-0
WEBADMIN_I_PKG=$(WEBADMIN_I)_$(WEBADMIN_I_VERSION)_$(ARCH).deb

ADC=adc
ADC_VERSION=1.0-1
ADC_PKG=$(ADC)_$(ADC_VERSION)_$(ARCH).deb

WIRE=one-wire
WIRE_VERSION=1.0-1
WIRE_PKG=$(WIRE)_$(WIRE_VERSION)_$(ARCH).deb

POWERWATCH=powerwatch
POWERWATCH_VERSION=1.1-0
POWERWATCH_PKG=$(POWERWATCH)_$(POWERWATCH_VERSION)_$(ARCH).deb

COUNTOUT=countout
COUNTOUT_VERSION=1.0-0
COUNTOUT_PKG=$(COUNTOUT)_$(COUNTOUT_VERSION)_$(ARCH).deb

SIM5360=sim5360
SIM5360_VERSION=1.1-1
SIM5360_PKG=$(SIM5360)_$(SIM5360_VERSION)_$(ARCH).deb

DS3231=ds3231
DS3231_VERSION=1.0-0
DS3231_PKG=$(DS3231)_$(DS3231_VERSION)_$(ARCH).deb

CFLAGS=$(shell pkg-config --cflags --libs python-3.4)
CFLAGS+=-fPIC -O2

all: $(NPORT) $(WRAPPER) $(ALTROUTE) $(MODEMWATCHDOG) $(WEBADMIN) $(WEBADMIN_I) $(ADC) $(WIRE) $(POWERWATCH) $(COUNTOUT) $(SIM5360) $(DS3231)

$(NPORT): $(NPORT_PKG)

$(NPORT_PKG): deb/DEBIAN/control deb/usr/bin/nport deb/var/lib/nport
	fakeroot dpkg-deb --build deb $@

deb/usr/bin/nport: Makefile main.py nport/__init__.py nport/TcpClient.py nport/VKT7Handler.py
	tar -c Makefile main.py nport/*.py | ssh debian@$(BBBIP) "cd /tmp; tar xf - ; make nport_out >& /dev/null ; tar -c main.bin nport/*.so nport/*.pyc" | tar -xf -
	mkdir -p deb/usr/bin
	mkdir -p $(PYLIB)
	cp nport/*.so nport/*.pyc nport/rfc2217.py $(PYLIB)/
	cp main.bin $@
	chmod +x $@

nport_out: main.bin nport/__init__.so nport/VKT7Handler.so nport/TcpClient.pyc

$(PYLIB) deb/var/lib/nport nport_armhf/var/lib/nport wrapper/var/lib/update-wrapper:
	mkdir -p $@

%.c: %.py
	cython3 -3 $<

main.c: main.py
	cython3 -3 --embed $<

%.so: %.c
	gcc $(CFLAGS) -shared $< -o $@
	strip -s $@

main.bin: main.c
	gcc $(CFLAGS) $< -o $@
	strip -s $@

%.pyc: %.py
	python3.4m -c "import py_compile; py_compile.compile('$<', '$@')"

%.pyc: $(PYCACHE)/%.cpython-34.pyc
	cp $< $@

deb/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

main.py: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WEBADMIN_I): $(WEBADMIN_I_PKG)

$(WEBADMIN_I_PKG): $(WEBADMIN_I)/DEBIAN/control
	fakeroot dpkg-deb --build $(WEBADMIN_I) $@

$(WEBADMIN_I)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(WEBADMIN_I_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(WEBADMIN_I_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WEBADMIN): $(WEBADMIN_PKG)

$(WEBADMIN_PKG): $(WEBADMIN)/DEBIAN/control
	fakeroot dpkg-deb --build $(WEBADMIN) $@

$(WEBADMIN)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(WEBADMIN_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(WEBADMIN_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WRAPPER): $(WRAPPER_PKG)

$(WRAPPER_PKG): $(WRAPPER)/DEBIAN/control $(WRAPPER)/usr/bin/update-wrapper $(WRAPPER)/usr/share/update-wrapper/update.sh $(WRAPPER)/var/lib/update-wrapper
	fakeroot dpkg-deb --build $(WRAPPER) $@

$(WRAPPER)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(WRAPPER_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(WRAPPER_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WRAPPER)/usr/bin/update-wrapper: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(WRAPPER_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(WRAPPER_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(ALTROUTE): $(ALTROUTE_PKG)

$(ALTROUTE_PKG): $(ALTROUTE)/DEBIAN/control $(ALTROUTE)/usr/bin/altroute $(ALTROUTE)/etc/default/altroute $(ALTROUTE)/etc/dhcp/dhclient-exit-hooks.d/altroute
	fakeroot dpkg-deb --build $(ALTROUTE) $@

$(ALTROUTE)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(ALTROUTE_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(ALTROUTE_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(ALTROUTE)/usr/bin/altroute: Makefile
	@if [ "`grep "version=" $@ | awk '{print $$2}'`" != "$(ALTROUTE_VERSION)" ] ; then \
		sed -i -e "s:version=.*:version=$(ALTROUTE_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(MODEMWATCHDOG): $(MODEMWATCHDOG_PKG)

$(MODEMWATCHDOG_PKG): $(MODEMWATCHDOG)/DEBIAN/control $(MODEMWATCHDOG)/usr/bin/modemwatchdog $(MODEMWATCHDOG)/etc/default/modemwatchdog
	fakeroot dpkg-deb --build $(MODEMWATCHDOG) $@

$(MODEMWATCHDOG)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(MODEMWATCHDOG_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(MODEMWATCHDOG_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(MODEMWATCHDOG)/usr/bin/modemwatchdog: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(MODEMWATCHDOG_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(MODEMWATCHDOG_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(ADC): $(ADC_PKG)

$(ADC_PKG): $(ADC)/DEBIAN/control $(ADC)/usr/bin/adc
	fakeroot dpkg-deb --build $(ADC) $@

$(ADC)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(ADC_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(ADC_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(ADC)/usr/bin/adc: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(ADC_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(ADC_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WIRE): $(WIRE_PKG)

$(WIRE_PKG): $(WIRE)/DEBIAN/control $(WIRE)/DEBIAN/postinst $(WIRE)/DEBIAN/postrm $(WIRE)/usr/bin/w1_bus_remove_hook $(WIRE)/lib/firmware/BB-W1-00A0.dtbo
	fakeroot dpkg-deb --build $(WIRE) $@

$(WIRE)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(WIRE_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(WIRE_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(WIRE)/usr/bin/w1_bus_remove_hook: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(WIRE_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(WIRE_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(POWERWATCH): $(POWERWATCH_PKG)

$(POWERWATCH_PKG): $(POWERWATCH)/DEBIAN/control $(POWERWATCH)/DEBIAN/postinst $(POWERWATCH)/usr/bin/powerwatch
	fakeroot dpkg-deb --build $(POWERWATCH) $@

$(POWERWATCH)/usr/bin/powerwatch: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(POWERWATCH_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(POWERWATCH_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(POWERWATCH)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(POWERWATCH_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(POWERWATCH_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(COUNTOUT): $(COUNTOUT_PKG)

$(COUNTOUT_PKG): $(COUNTOUT)/DEBIAN/control $(COUNTOUT)/usr/bin/countout
	fakeroot dpkg-deb --build $(COUNTOUT) $@

$(COUNTOUT)/usr/bin/countout: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(COUNTOUT_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(COUNTOUT_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(COUNTOUT)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(COUNTOUT_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(COUNTOUT_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(SIM5360): $(SIM5360_PKG)

$(SIM5360_PKG): $(SIM5360)/DEBIAN/control $(SIM5360)/usr/bin/sim5360
	fakeroot dpkg-deb --build $(SIM5360) $@

$(SIM5360)/usr/bin/sim5360: Makefile
	@if [ "`grep "version =" $@ | awk '{print $$3}'`" != "\"$(SIM5360_VERSION)\"" ] ; then \
		sed -i -e "s:version =.*:version = \"$(SIM5360_VERSION)\":g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(SIM5360)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(SIM5360_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(SIM5360_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

$(DS3231): $(DS3231_PKG)

$(DS3231_PKG): $(DS3231)/DEBIAN/control $(DS3231)/etc/udev/rules.d/80-ds3231.rules
	fakeroot dpkg-deb --build $(DS3231) $@

$(DS3231)/DEBIAN/control: Makefile
	@if [ "`grep "Version:" $@ | awk '{print $$2}'`" != "$(DS3231_VERSION)" ] ; then \
		sed -i -e "s:Version\:.*:Version\: $(DS3231_VERSION):g" $@ ; \
		if [ -e $@-e ] ; then rm $@-e ; fi ; \
	fi

