FROM gentoo/stage3

RUN echo 'ACCEPT_KEYWORDS="~amd64"' >> /etc/portage/make.conf
RUN echo 'ACCEPT_LICENSE="*"' >> /etc/portage/make.conf
RUN echo 'EMERGE_DEFAULT_OPTS="--autounmask=y --autounmask-continue=y --jobs"' >> /etc/portage/make.conf
RUN echo 'MAKEOPTS="-j4"' >> /etc/portage/make.conf

RUN emerge-webrsync
RUN emerge --update --deep --newuse @world
RUN emerge --onlydeps www-client/google-chrome-unstable
