try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree


class TagDescriptor(object):
    def __get__(_self, _instance, cls):
        return getattr(cls, '__tag__', None) or cls.__name__


class Node(object):
    tag = TagDescriptor()

    def __init__(self, **attributes):
        self.attributes = attributes.copy()
        self.children = []

    def __call__(self, *children):
        self.children = list(children)
        return self

    def get_node(self, creator):
        attributes = self.attributes
        if 'type' in attributes:
            attributes = attributes.copy()
            etype = attributes['type']
            attributes['type'] = creator.get_prefixed_tag(etype.namespace, etype.tag)

        node = creator(self.__class__.namespace, self.tag, attributes)
        for child in self.children:
            node.append(child.get_node(creator))

        return node


class Type(Node):
    class InstanceClassDescriptor(object):
        def __init__(self):
            self.cache = {}

        def __get__(self, _instance, cls):
            try:
                return self.cache[cls]
            except KeyError:
                pass

            result = self.cache[cls] = create_instance_class(cls)
            return result

    @classmethod
    def get_name(cls):
        return cls.__name__

    instance_class = InstanceClassDescriptor()


class Namespace(object):
    def __init__(self, namespace, abbr=None):
        self.namespace = namespace
        self.abbr = abbr


class Instance(object):
    def __init__(self, element, *args, **kwargs):
        self._element = element
        self._type.init(self, *args, **kwargs)

    def get_node(self, creator):
        node = creator(self._element.schema.targetNamespace, self._element.name)
        self._type.fill_node(node, self, creator)
        return node


def create_instance_class(etype):
    fields = {}
    name = etype.get_name() + 'Instance'
    fields['_type'] = etype

    return type(name, (Instance,), fields)

def get_root(node_getter):
    creator = ElementCreator()
    node = node_getter.get_node(creator)
    for uri, prefix in creator.prefixes.iteritems():
        node.attrib['xmlns:%s' % prefix] = uri

    return node


class ElementCreator(object):
    def __init__(self):
        self.ns_counter = 0
        self.prefixes = {}

    def get_prefix(self, namespace):
        try:
            return self.prefixes[namespace.namespace]
        except KeyError:
            pass

        if namespace.abbr:
            prefix = namespace.abbr
        else:
            prefix = 'ns%d' % self.ns_counter
            self.ns_counter += 1

        self.prefixes[namespace.namespace] = prefix
        return prefix

    def get_prefixed_tag(self, namespace, tag):
        return '{}:{}'.format(self.get_prefix(namespace), tag)

    def __call__(self, namespace, tag, *args, **kwargs):
        return etree.Element(self.get_prefixed_tag(namespace, tag), *args, **kwargs)