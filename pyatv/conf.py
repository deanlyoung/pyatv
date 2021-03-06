"""Configuration when connecting to an Apple TV."""

from pyatv import convert
from pyatv.const import (PROTOCOL_MRP, PROTOCOL_DMAP, PROTOCOL_AIRPLAY)

_SUPPORTED_PROTOCOLS = [PROTOCOL_MRP, PROTOCOL_DMAP]


class AppleTV:
    """Representation of an Apple TV configuration.

    An instance of this class represents a single device. A device can have
    several services, depending on the protocols it supports, e.g. DMAP or
    AirPlay.
    """

    def __init__(self, address, name, **kwargs):
        """Initialize a new AppleTV."""
        self.address = address
        self.name = name
        self._services = {}
        self._supported_protocols = \
            kwargs.get('supported_services', _SUPPORTED_PROTOCOLS)

    def add_service(self, service):
        """Add a new service.

        If the service already exists, it will be replaced.
        """
        if service.protocol in self._services:
            existing = self._services[service.protocol]
            if not existing.superseeded_by(service):
                return

        self._services[service.protocol] = service

    def get_service(self, protocol):
        """Look up a service based on protocol.

        If a service with the specified protocol is not available, None is
        returned.
        """
        return self._services.get(protocol, None)

    def services(self):
        """Return all supported services."""
        return list(self._services.values())

    def usable_service(self):
        """Return a usable service or None if there is none.

        A service is usable if enough configuration to be able to make a
        connection is available. If several protocols are usable, MRP will be
        preferred over DMAP.
        """
        services = self._services
        for protocol in self._supported_protocols:
            if protocol in services and services[protocol].is_usable():
                return services[protocol]

        return None

    def preferred_service(self):
        """Return the best supported service of the device.

        This methods works similarily to usable_service(), but it will return
        the most appropriate service regardless of it being usable or not. So
        an Apple TV supporting both DMAP and MRP (like gen 4) will return MRP
        here.
        """
        for protocol in self._supported_protocols:
            if protocol in self._services:
                return self._services[protocol]

        return None

    def is_usable(self):
        """Return True if there are any usable services."""
        return any([x.is_usable() for x in self._services.values()])

    def airplay_service(self):
        """Return service used for AirPlay.

        If no AirPlay service has been found, a default at port 7000 will be
        created.
        """
        if PROTOCOL_AIRPLAY in self._services:
            return self._services[PROTOCOL_AIRPLAY]
        return AirPlayService(7000)

    def __eq__(self, other):
        """Compare instance with another instance."""
        if isinstance(other, self.__class__):
            print(self.address == other.address)
            return self.address == other.address
        return False

    def __str__(self):
        """Return a string representation of this object."""
        services = [' - {0}'.format(s) for s in self._services.values()]
        return 'Device "{0}" at {1} supports these services:\n{2}'.format(
            self.name, self.address, '\n'.join(services))


# pylint: disable=too-few-public-methods
class BaseService:
    """Base class for protocol services."""

    def __init__(self, protocol, port):
        """Initialize a new BaseService."""
        self.protocol = protocol
        self.port = port

    @staticmethod
    def is_usable():
        """Return True if service is usable, else False."""
        return False

    # pylint: disable=unused-argument
    @staticmethod
    def superseeded_by(other_service):
        """Return True if input service should be used instead of this one."""
        return False

    def __str__(self):
        """Return a string representation of this object."""
        return 'Protocol: {0}, Port: {1}'.format(
            convert.protocol_str(self.protocol), self.port)


# pylint: disable=too-few-public-methods
class DmapService(BaseService):
    """Representation of a DMAP service."""

    def __init__(self, login_id, port=None):
        """Initialize a new DmapService."""
        super().__init__(PROTOCOL_DMAP, port or 3689)
        self.login_id = login_id

    def is_usable(self):
        """Return True if service is usable, else False."""
        return self.login_id is not None

    def superseeded_by(self, other_service):
        """Return True if input service has login id and this has not."""
        if not other_service or \
                other_service.__class__ != self.__class__ or \
                other_service.protocol != self.protocol or \
                other_service.port != self.port:
            return False

        # If this service does not have a login id but the other one does, then
        # we should return True here
        return not self.login_id and other_service.login_id

    def __str__(self):
        """Return a string representation of this object."""
        return super().__str__() + ', Login ID: {0}'.format(self.login_id)


# pylint: disable=too-few-public-methods
class MrpService(BaseService):
    """Representation of a MediaRemote Protocol service."""

    def __init__(self, port):
        """Initialize a new MrpService."""
        super().__init__(PROTOCOL_MRP, port)

    def is_usable(self):
        """Return True if service is usable, else False."""
        return True


# pylint: disable=too-few-public-methods
class AirPlayService(BaseService):
    """Representation of an AirPlay service."""

    def __init__(self, port):
        """Initialize a new AirPlayService."""
        super().__init__(PROTOCOL_AIRPLAY, port)
