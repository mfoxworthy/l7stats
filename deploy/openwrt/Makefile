include $(TOPDIR)/rules.mk

PKG_NAME:=l7stats
PKG_SOURCE_VERSION:=v1.0
PKG_VERSION:=v1.0
PKG_RELEASE:=1
PKG_MAINTAINER:=Michael Foxworthy <mfoxworthy@ipsquared.com>

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=git@github.com:mfoxworthy/l7stats.git
PKG_MIRROR_HASH:=skip

PKG_LICENSE:=GPLv3



include $(INCLUDE_DIR)/package.mk

define Package/l7stats
  SECTION:=net
  CATEGORY:=Network
  DEPENDS:=
#	DEPENDS:=+netifyd +python3-urllib +python3-openssl +python3-codecs +python3-ctypes +collectd +luci-app-statistics +collectd-mod-unixsock
  TITLE:=l7stats - Layer 7 Statistics for luci-app-statistics
  PKGARCH:=all
endef

define Package/l7stats/description
  Layer 7 statistics provides a socket writer to collectd unix socket reader. From there, collectd writers
  can write the data to any write plugin. This application uses the RRD collectd plugin to provide the statistics
  application with data.
endef

define Build/Prepare
endef

define Build/Configure
endef

define Build/Compile
endef


define Package/l7stats/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./deploy/openwrt/files/l7stats.init  $(1)/etc/init.d/l7stats

	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./deploy/openwrt/files/l7stats.sh $(1)/usr/sbin

	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) ./deploy/openwrt/files/l7stats.config  $(1)/etc/config/l7stats

	$(INSTALL_DIR) $(1)/usr/share/l7stats
	$(CP) *.py $(1)/usr/share/l7stats/
endef

define Package/l7stats/postinst
#!/bin/sh
/etc/init.d/l7stats enable
/etc/init.d/l7stats start
exit 0
endef

$(eval $(call BuildPackage,l7stats))