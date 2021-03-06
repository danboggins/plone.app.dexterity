from Products.ATContentTypes import permission as ATCTPermissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

# constants for enableConstrain. Copied from AT
ACQUIRE = -1  # acquire locallyAllowedTypes from parent (default)
DISABLED = 0  # use default behavior of PortalFolder which uses the FTI info
ENABLED = 1  # allow types from locallyAllowedTypes only


class ConstrainTypesBehavior(object):

    def __init__(self, context):
        self.context = context

    def getConstrainTypesMode(self):
        """
        If value is set, use it.
        Default value is ACQUIRED, IF the parent is of the same portal type
        and can be adapted to ISelectableConstrainTypes.
        Else it is DISABLED
        """
        if hasattr(self.context, 'constrain_types_mode'):
            return self.context.constrain_types_mode
        parent = self.context.__parent__
        if not parent:
            return DISABLED
        if not self.context.portal_type == parent.portal_type:
            return DISABLED
        if not ISelectableConstrainTypes(parent, None):
            return DISABLED
        return ACQUIRE

    def setConstrainTypesMode(self, mode):
        if mode not in [ACQUIRE, DISABLED, ENABLED]:
            raise ValueError()
        self.context.constrain_types_mode = mode

    def canSetConstrainTypes(self):
        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return member.has_permission(
            ATCTPermissions.ModifyConstrainTypes, self.context)

    def getDefaultAddableTypes(self):
        return self._getAddableTypesFor(self.context, self.context)

    def _getAddableTypesFor(self, obj, context):
        """
        return the addable types that are generally
        allowed for the type of `obj` and that have valid constructor
        information in the types tool and for that the current user
        has the correct add permission in the context of `context`
        """
        portal_types = getToolByName(context, 'portal_types')
        my_type = portal_types.getTypeInfo(obj)
        result = portal_types.listTypeInfo()
        return [t for t in result if my_type.allowType(t.getId()) and
                t.isConstructionAllowed(context)]

    def _filterByDefaults(self, types):
        """
        Filter the given types by the items which would also be allowed by
        default. Important, else users could circumvent security restritions
        """
        defaults = [fti.getId() for fti in self.getDefaultAddableTypes()]
        return [x for x in types if x in defaults]

    def allowedContentTypes(self):
        """
        If constraints are enabled, return the locally allowed types.
        If the setting is ACQUIRE, acquire the locally allowed types according
        to the ACQUIRE rules, described in the interface.
        If constraints are disabled, use the default addable types

        This method returns the FTI, NOT the FTI id, like most other methods.
        """
        mode = self.getConstrainTypesMode()
        default_addable = self.getDefaultAddableTypes()

        if mode == DISABLED:
            return default_addable
        elif mode == ENABLED:
            if hasattr(self.context, 'locally_allowed_types'):
                return [t for t in default_addable if t.getId() in
                        self.context.locally_allowed_types]
            else:
                return default_addable
        elif mode == ACQUIRE:
            parent = self.context.__parent__
            parent_constrain_adapter = ISelectableConstrainTypes(parent, None)
            if not parent_constrain_adapter:
                return default_addable
            return_tids = self._filterByDefaults(
                parent_constrain_adapter.getLocallyAllowedTypes())
            return [t for t in default_addable if t.getId() in return_tids]
        else:
            raise Exception(
                "Wrong constraint setting. %i is an invalid value",
                mode)

    def getLocallyAllowedTypes(self):
        """
        If constraints are enabled, return the locally allowed types.
        If the setting is ACQUIRE, acquire the locally allowed types according
        to the ACQUIRE rules, described in the interface.
        If constraints are disabled, use the default addable types
        """
        return [t.getId() for t in self.allowedContentTypes()]

    def setLocallyAllowedTypes(self, types):
        defaults = [t.getId() for t in self.getDefaultAddableTypes()]
        for type_ in types:
            if type_ not in defaults:
                raise ValueError("%s is not a valid type id", type_)
        self.context.locally_allowed_types = types

    def getImmediatelyAddableTypes(self):
        """
        If constraints are enabled, return the locally immediately
        addable tpes.
        If the setting is ACQUIRE, acquire the immediately addable types from
        the parent, according to the rules described in the interface.
        If constraints are disabled, use the default addable types
        """
        mode = self.getConstrainTypesMode()
        default_addable = [t.getId() for t in self.getDefaultAddableTypes()]

        if mode == DISABLED:
            return default_addable
        elif mode == ENABLED:
            if hasattr(self.context, 'immediately_addable_types'):
                return self._filterByDefaults(
                    self.context.immediately_addable_types)
        elif mode == ACQUIRE:
            parent = self.context.__parent__
            parent_constrain_adapter = ISelectableConstrainTypes(parent, None)
            if not parent_constrain_adapter:
                return default_addable
            return self._filterByDefaults(
                parent_constrain_adapter.getImmediatelyAddableTypes())
        else:
            raise Exception(
                "Wrong constraint setting. %i is an invalid value",
                mode)

    def setImmediatelyAddableTypes(self, types):
        defaults = [t.getId() for t in self.getDefaultAddableTypes()]
        for type_ in types:
            if type_ not in defaults:
                raise ValueError("%s is not a valid type id", type_)
        self.context.immediately_addable_types = types
