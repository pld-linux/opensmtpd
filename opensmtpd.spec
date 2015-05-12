# TODO
# - should mailq and newaliases be in bindir?

# Conditional build:
%bcond_without	pam		# build without PAM support

Summary:	Free implementation of the server-side SMTP protocol as defined by RFC 5321
Name:		opensmtpd
Version:	5.4.5p1
Release:	1
License:	ISC
Group:		Daemons
Source0:	https://www.opensmtpd.org/archives/%{name}-%{version}.tar.gz
# Source0-md5:	05b58cecf0d6c2f385954b94d85e271a
Source1:	%{name}.service
Source2:	%{name}.init
Source3:	%{name}.pam
Source4:	aliases
URL:		http://www.opensmtpd.org/
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	bison
BuildRequires:	db-devel
BuildRequires:	libasr-devel
BuildRequires:	libevent-devel
BuildRequires:	openssl-devel
%{?with_pam:BuildRequires:	pam-devel}
BuildRequires:	rpmbuild(macros) >= 1.228
BuildRequires:	zlib-devel
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	rc-scripts
Suggests:	ca-certificates
Provides:	group(smtpd)
Provides:	group(smtpq)
Provides:	smtpdaemon
Provides:	user(smtpd)
Provides:	user(smtpq)
Obsoletes:	smtpdaemon
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		privsepdir	/usr/share/empty
%define		spooldir	/var/spool/smtpd
%define		certsdir	/etc/certs

%description
OpenSMTPD is a FREE implementation of the server-side SMTP protocol as
defined by RFC 5321, with some additional standard extensions. It
allows ordinary machines to exchange e-mails with other systems
speaking the SMTP protocol.

Started out of dissatisfaction with other implementations, OpenSMTPD
nowadays is a fairly complete SMTP implementation. OpenSMTPD is
primarily developed by Gilles Chehade, Eric Faurot and Charles
Longeau; with contributions from various OpenBSD hackers. OpenSMTPD is
part of the OpenBSD Project. The software is freely usable and
re-usable by everyone under an ISC license.

%prep
%setup -q

%build
%{__aclocal}
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	--sysconfdir=%{_sysconfdir}/mail \
	--with-ca-file=%{certsdir}/ca-certificates.crt \
	--with-mantype=man \
	%{?with_pam:--with-pam} \
	--with-privsep-user=smtpd \
	--with-queue-user=smtpq \
	--with-privsep-path=%{privsepdir} \
	--with-sock-dir=%{_localstatedir}/run

%{__make}

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT{%{systemdunitdir},/etc/{rc.d/init.d,pam.d}}
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdunitdir}/opensmtpd.service
install -p %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/opensmtpd
cp -p %{SOURCE4} $RPM_BUILD_ROOT/etc/mail
%if %{with pam}
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/pam.d/smtp
%endif
touch $RPM_BUILD_ROOT%{_sysconfdir}/mail/aliases.db

# /usr/sbin/sendmail compatibility is not required /usr/lib/sendmail is
install -d $RPM_BUILD_ROOT%{_prefix}/lib
mv $RPM_BUILD_ROOT{%{_bindir},%{_prefix}/lib}/sendmail

# queue dirs
install -d $RPM_BUILD_ROOT%{spooldir}/{queue,corrupt,incoming,offline,purge,temporary}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 297 smtpd
%groupadd -g 298 smtpq
%useradd -u 297 -g smtpd -s /sbin/nologin -c "OpenSMTPd privsep user" -d %{privsepdir} smtpd
%useradd -u 298 -g smtpq -s /sbin/nologin -c "OpenSMTPd queue user" -d %{privsepdir} smtpq

%post
/sbin/chkconfig --add %{name}
%service %{name} restart
%systemd_post %{name}.service

%preun
if [ $1 = 0 ]; then
	%service %{name} stop
	/sbin/chkconfig --del %{name}
fi
%systemd_preun %{name}.service

%postun
if [ "$1" = "0" ]; then
	%userremove smtpd
	%userremove smtpq
	%groupremove smtpd
	%groupremove smtpq
fi
%systemd_reload

%files
%defattr(644,root,root,755)
%doc LICENSE README.md THANKS
%dir %{_sysconfdir}/mail
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/mail/smtpd.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/mail/aliases
%ghost %{_sysconfdir}/mail/aliases.db
%if %{with pam}
%config(noreplace) %verify(not md5 mtime size) /etc/pam.d/smtp
%endif
%attr(754,root,root) /etc/rc.d/init.d/opensmtpd
%{systemdunitdir}/%{name}.service
%attr(755,root,root) %{_sbindir}/mailq
%attr(755,root,root) %{_sbindir}/makemap
%attr(755,root,root) %{_sbindir}/newaliases
%attr(755,root,root) %{_sbindir}/smtpctl
%attr(755,root,root) %{_sbindir}/smtpd
%attr(755,root,root) %{_prefix}/lib/sendmail
%{_mandir}/man5/aliases.5*
%{_mandir}/man5/forward.5*
%{_mandir}/man5/smtpd.conf.5*
%{_mandir}/man5/table.5*
%{_mandir}/man8/makemap.8*
%{_mandir}/man8/newaliases.8*
%{_mandir}/man8/sendmail.8*
%{_mandir}/man8/smtpctl.8*
%{_mandir}/man8/smtpd.8*
%dir %{_libdir}/%{name}
%attr(755,root,root) %{_libdir}/%{name}/encrypt
%attr(755,root,root) %{_libdir}/%{name}/mail.local

%dir %attr(711,root,root) %{spooldir}
%dir %attr(1777,root,root) %{spooldir}/offline
%dir %attr(700,smtpq,root) %{spooldir}/corrupt
%dir %attr(700,smtpq,root) %{spooldir}/incoming
%dir %attr(700,smtpq,root) %{spooldir}/purge
%dir %attr(700,smtpq,root) %{spooldir}/queue
%dir %attr(700,smtpq,root) %{spooldir}/temporary
