# TODO
# - should mailq and newaliases be in bindir?
#
# Conditional build:
%bcond_without	pam		# build without PAM support
%bcond_without	table_db	# build table-db backend

Summary:	Free implementation of the server-side SMTP protocol as defined by RFC 5321
Summary(pl.UTF-8):	Wolnodostępna implementacja strony serwerowej protokołu SMTP wg RFC 5321
Name:		opensmtpd
Version:	6.6.2p1
Release:	1
License:	ISC
Group:		Daemons
Source0:	https://www.opensmtpd.org/archives/%{name}-%{version}.tar.gz
# Source0-md5:	bd29619f56c009a4eb4879304771822b
Source1:	%{name}.service
Source2:	%{name}.init
Source3:	%{name}.pam
Source4:	aliases
Patch0:		%{name}-ac.patch
URL:		https://www.opensmtpd.org/
BuildRequires:	autoconf >= 2.69
BuildRequires:	automake
BuildRequires:	bison
%{?with_table_db:BuildRequires:	db-devel}
BuildRequires:	libasr-devel
BuildRequires:	libevent-devel
BuildRequires:	libtool >= 2:2
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
%requires_ge_to	openssl	openssl-devel
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
%patch0 -p1

%build
%{__libtoolize}
%{__aclocal} -I m4
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	--sysconfdir=%{_sysconfdir}/mail \
	%{?with_pam:--with-auth-pam=smtp} \
	--with-group-queue=smtpq \
	--with-mantype=man \
	--with-path-CAfile=%{certsdir}/ca-certificates.crt \
	--with-path-empty=%{privsepdir} \
	%{?with_table_db:--with-table-db} \
	--with-user-queue=smtpq \
	--with-user-smtpd=smtpd

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

install -d $RPM_BUILD_ROOT%{_prefix}/lib
ln -s %{_sbindir}/smtpctl $RPM_BUILD_ROOT%{_prefix}/lib/sendmail

# other utils
ln -s %{_sbindir}/smtpctl $RPM_BUILD_ROOT%{_sbindir}/mailq
ln -s %{_sbindir}/smtpctl $RPM_BUILD_ROOT%{_sbindir}/sendmail
%if %{with table_db}
ln -s %{_sbindir}/smtpctl $RPM_BUILD_ROOT%{_sbindir}/makemap
ln -s %{_sbindir}/smtpctl $RPM_BUILD_ROOT%{_sbindir}/newaliases
%endif

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
%doc LICENSE README.md
%dir %{_sysconfdir}/mail
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/mail/smtpd.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/mail/aliases
%if %{with table_db}
%ghost %{_sysconfdir}/mail/aliases.db
%endif
%if %{with pam}
%config(noreplace) %verify(not md5 mtime size) /etc/pam.d/smtp
%endif
%attr(754,root,root) /etc/rc.d/init.d/opensmtpd
%{systemdunitdir}/%{name}.service
%attr(755,root,root) %{_bindir}/smtp
%attr(755,root,root) %{_sbindir}/mailq
%attr(755,root,root) %{_sbindir}/sendmail
%attr(755,root,root) %{_sbindir}/smtpctl
%attr(755,root,root) %{_sbindir}/smtpd
%attr(755,root,root) %{_prefix}/lib/sendmail
%{_mandir}/man1/smtp.1*
%{_mandir}/man5/aliases.5*
%{_mandir}/man5/forward.5*
%{_mandir}/man5/smtpd.conf.5*
%{_mandir}/man5/table.5*
%{_mandir}/man8/sendmail.8*
%{_mandir}/man8/smtpctl.8*
%{_mandir}/man8/smtpd.8*

%if %{with table_db}
%attr(755,root,root) %{_sbindir}/makemap
%attr(755,root,root) %{_sbindir}/newaliases
%{_mandir}/man8/makemap.8*
%{_mandir}/man8/newaliases.8*
%endif

%dir %{_libexecdir}/%{name}
%attr(755,root,root) %{_libexecdir}/%{name}/encrypt
%attr(755,root,root) %{_libexecdir}/%{name}/mail.lmtp
%attr(755,root,root) %{_libexecdir}/%{name}/mail.local
%attr(755,root,root) %{_libexecdir}/%{name}/mail.maildir
%attr(755,root,root) %{_libexecdir}/%{name}/mail.mboxfile
%attr(755,root,root) %{_libexecdir}/%{name}/mail.mda

%dir %attr(711,root,root) %{spooldir}
%dir %attr(770,root,smtpq) %{spooldir}/offline
%dir %attr(700,smtpq,root) %{spooldir}/corrupt
%dir %attr(700,smtpq,root) %{spooldir}/incoming
%dir %attr(700,smtpq,root) %{spooldir}/purge
%dir %attr(700,smtpq,root) %{spooldir}/queue
%dir %attr(700,smtpq,root) %{spooldir}/temporary
