include $(TOPDIR)/rules.mk

PKG_NAME:=l7stats
PKG_SOURCE_VERSION:=542ca21c49f8768ed5cba2e738bfb6700ceb47ed
PKG_SOURCE_DATE=2022-03-03
PKG_RELEASE:=v1.1
PKG_MAINTAINER:=Michael Foxworthy <mfoxworthy@ipsquared.com>

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=git@github.com:mfoxworthy/l7stats.git
PKG_MIRROR_HASH:=b12047b0b01b9bb27fdfa86a53f14eaa175f104bd33f530e2e699d815d39b1c7

PKG_LICENSE:=GPLv3

include $(INCLUDE_DIR)/package.mk

define Package/l7stats
  SECTION:=net
  CATEGORY:=Network
  DEPENDS:=+netifyd +python3-urllib +python3-openssl +collectd +collectd-mod-unixsock
  TITLE:=l7stats - Layer 7 Statistics for luci-app-statistics
  PKGARCH:=all
endef

define Package/l7stats/description
  Layer 7 statistics provides a socket writer to collectd unix socket reader. From there, collectd writers
  can write the data to any write plugin. This application uses the RRD collectd plugin to provide the statistics
  application with data.
endef


define Build/Compile
endef


define Package/l7stats/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/deploy/openwrt/files/l7stats.init  $(1)/etc/init.d/l7stats

	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/deploy/openwrt/files/l7stats.sh $(1)/usr/sbin

	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/openwrt/files/l7stats.config  $(1)/etc/config/l7stats

	$(INSTALL_DIR) $(1)/usr/share/l7stats
	$(CP) $(PKG_BUILD_DIR)/*.py $(1)/usr/share/l7stats/
endef

define Package/l7stats/postinst
#!/bin/sh
/etc/init.d/l7stats enable
/etc/init.d/l7stats start
exit 0
endef

$(eval $(call BuildPackage,l7stats))