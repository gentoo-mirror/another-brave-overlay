FROM gentoo/stage3

RUN echo 'ACCEPT_KEYWORDS="~amd64"' >> /etc/portage/make.conf
RUN echo 'ACCEPT_LICENSE="*"' >> /etc/portage/make.conf
RUN echo 'EMERGE_DEFAULT_OPTS="--autounmask=y --autounmask-continue=y --jobs=$(nproc)"' >> /etc/portage/make.conf
RUN echo 'MAKEOPTS="-j$(nproc)"' >> /etc/portage/make.conf
RUN echo 'FEATURES="-pid-sandbox -ipc-sandbox -network-sandbox"' >> /etc/portage/make.conf

RUN emerge-webrsync
RUN emerge --update --deep --newuse -v @world
RUN emerge --onlydeps -v www-client/google-chrome-unstable
