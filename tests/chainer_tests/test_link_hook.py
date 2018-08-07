import unittest

import numpy

import chainer
from chainer import testing


class MyLinkHook(chainer.LinkHook):
    name = 'MyLinkHook'

    def __init__(self):
        self.added_args = []
        self.deleted_args = []
        self.forward_preprocess_args = []
        self.forward_postprocess_args = []

    def added(self, link):
        assert link is None or isinstance(link, chainer.Link)
        self.added_args.append(link)

    def deleted(self, link):
        assert link is None or isinstance(link, chainer.Link)
        self.deleted_args.append(link)

    def forward_preprocess(self, args):
        assert isinstance(args.link, chainer.Link)
        assert isinstance(args.forward_name, str)
        assert isinstance(args.args, tuple)
        assert isinstance(args.kwargs, dict)
        assert isinstance(str(args), str)
        assert isinstance(repr(args), str)
        self.forward_preprocess_args.append(args)

    def forward_postprocess(self, args):
        assert isinstance(args.link, chainer.Link)
        assert isinstance(args.forward_name, str)
        assert isinstance(args.args, tuple)
        assert isinstance(args.kwargs, dict)
        assert hasattr(args, 'out')
        assert isinstance(str(args), str)
        assert isinstance(repr(args), str)
        self.forward_postprocess_args.append(args)


class MyModel(chainer.Chain):
    def __init__(self, w):
        super(MyModel, self).__init__()
        with self.init_scope():
            self.l1 = chainer.links.Linear(3, 2, initialW=w)

    def forward(self, x, test1, test2):
        return self.l1(x)


class TestLinkHook(unittest.TestCase):

    def _create_model_and_data(self):
        x = numpy.array([[3, 1, 2]], numpy.float32)
        w = numpy.array([[1, 3, 2], [6, 4, 5]], numpy.float32)
        dot = numpy.dot(x, w.T)

        model = MyModel(w)

        return model, x, dot

    def test_name(self):
        chainer.LinkHook().name == 'LinkHook'

    def test_global_hook(self):
        model, x, dot = self._create_model_and_data()
        hook = MyLinkHook()

        with hook:
            model(chainer.Variable(x), 'foo', test2='bar')

        # added
        assert len(hook.added_args) == 1
        assert hook.added_args[0] is None

        # deleted
        assert len(hook.added_args) == 1
        assert hook.deleted_args[0] is None

        # forward_preprocess
        assert len(hook.forward_preprocess_args) == 2
        # - MyModel
        args = hook.forward_preprocess_args[0]
        assert args.link is model
        assert args.forward_name == 'forward'
        assert len(args.args) == 2
        numpy.testing.assert_array_equal(args.args[0].data, x)
        assert args.args[1] == 'foo'
        assert len(args.kwargs) == 1
        assert args.kwargs['test2'] == 'bar'
        # - Linear
        args = hook.forward_preprocess_args[1]
        assert args.link is model.l1
        assert args.forward_name == 'forward'

        # forward_postprocess
        assert len(hook.forward_postprocess_args) == 2
        # - Linear
        args = hook.forward_postprocess_args[0]
        assert args.link is model.l1
        assert args.forward_name == 'forward'
        # - MyModel
        args = hook.forward_postprocess_args[1]
        assert args.link is model
        assert args.forward_name == 'forward'
        assert len(args.args) == 2
        numpy.testing.assert_array_equal(args.args[0].data, x)
        assert args.args[1] == 'foo'
        assert len(args.kwargs) == 1
        assert args.kwargs['test2'] == 'bar'
        numpy.testing.assert_array_equal(args.out.data, dot)

    def _check_local_hook(self, add_hook_name, delete_hook_name):
        model, x, dot = self._create_model_and_data()
        hook = MyLinkHook()

        model.add_hook(hook, add_hook_name)
        model(chainer.Variable(x), 'foo', test2='bar')
        model.delete_hook(delete_hook_name)

        # added
        assert len(hook.added_args) == 1
        assert hook.added_args[0] is model

        # deleted
        assert len(hook.added_args) == 1
        assert hook.deleted_args[0] is model

        # forward_preprocess
        assert len(hook.forward_preprocess_args) == 1
        # - MyModel
        args = hook.forward_preprocess_args[0]
        assert args.link is model
        assert args.forward_name == 'forward'
        assert len(args.args) == 2
        numpy.testing.assert_array_equal(args.args[0].data, x)
        assert args.args[1] == 'foo'
        assert len(args.kwargs) == 1
        assert args.kwargs['test2'] == 'bar'

        # forward_postprocess
        assert len(hook.forward_postprocess_args) == 1
        # - MyModel
        args = hook.forward_postprocess_args[0]
        assert args.link is model
        assert args.forward_name == 'forward'
        assert len(args.args) == 2
        numpy.testing.assert_array_equal(args.args[0].data, x)
        assert args.args[1] == 'foo'
        assert len(args.kwargs) == 1
        assert args.kwargs['test2'] == 'bar'
        numpy.testing.assert_array_equal(args.out.data, dot)

    def test_local_hook_named(self):
        self._check_local_hook('myhook', 'myhook')

    def test_local_hook_unnamed(self):
        self._check_local_hook(None, 'MyLinkHook')

    def test_global_hook_delete(self):
        # Deleted hook should not be called

        model, x, dot = self._create_model_and_data()
        hook = MyLinkHook()

        with hook:
            pass
        model(chainer.Variable(x), 'foo', test2='bar')

        assert len(hook.added_args) == 1
        assert len(hook.deleted_args) == 1
        assert len(hook.forward_preprocess_args) == 0
        assert len(hook.forward_postprocess_args) == 0

    def test_local_hook_delete(self):
        # Deleted hook should not be called

        model, x, dot = self._create_model_and_data()
        hook = MyLinkHook()

        model.add_hook(hook)
        model.delete_hook('MyLinkHook')
        model(chainer.Variable(x), 'foo', test2='bar')

        assert len(hook.added_args) == 1
        assert len(hook.deleted_args) == 1
        assert len(hook.forward_preprocess_args) == 0
        assert len(hook.forward_postprocess_args) == 0


testing.run_module(__name__, __file__)
