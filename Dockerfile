FROM gentoo/stage3

RUN echo 'ACCEPT_KEYWORDS="~amd64"' >> /etc/portage/make.conf
RUN echo 'ACCEPT_LICENSE="*"' >> /etc/portage/make.conf
RUN echo 'EMERGE_DEFAULT_OPTS="--autounmask=y --autounmask-continue=y --getbinpkg --usepkg --jobs='$(nproc)'"' >> /etc/portage/make.conf
RUN echo 'MAKEOPTS="-j'$(nproc)'"' >> /etc/portage/make.conf
RUN echo 'FEATURES="getbinpkg -pid-sandbox -ipc-sandbox -network-sandbox"' >> /etc/portage/make.conf

RUN mkdir -p /etc/portage/binrepos.conf/
RUN echo "[binhost]" > /etc/portage/binrepos.conf/gentoobinhost.conf && \
    echo "priority = 9999" >> /etc/portage/binrepos.conf/gentoobinhost.conf && \
    echo "sync-uri = https://distfiles.gentoo.org/releases/amd64/binpackages/23.0/x86-64/" >> /etc/portage/binrepos.conf/gentoobinhost.conf

#RUN emaint sync -a
RUN emaint sync -r gentoo &> /dev/null && emaint sync -r binhost

RUN emerge --update --deep --newuse -v @world
RUN emerge --onlydeps -v www-client/google-chrome-unstable
