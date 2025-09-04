import sys
import io
import contextlib
import ast

### yerba
import json
import operator

inputs = []
current_input = 0

def readLine(*args):
    return readOverwrite()

def readInt(*args):
    return readOverwrite()

def readFloat(*args):
    return readOverwrite()

def input(*args):
    return readOverwrite()

def readOverwrite():
    global current_input
    global inputs
    try:
        val = inputs[current_input]
    except IndexError:
        val = 0
    else:
        current_input += 1
    return val


class expect(object):

    """Represents a logical expectation.

    """

    # a static class variable for storing all expectations
    expectations = []

    def __init__(self, actual, negated=False):
        """Create an expectation.

        Parameters
        ----------
        actual: primitive
            The actual on which we're making expectations.
        negated: boolean
            Indicates if the expectation should be false.

        """
        self.negated = negated
        self.actual = actual

        self.override_test_name = ''
        self.override_solution_output = ''
        self.override_student_output = ''
        self.override_message_pass = ''
        self.override_message_fail = ''
        self.override_show_diff = ''

    def __call__(self):
        """Evaluate the expectation."""
        return self.assertion()

    def __make_assertion(self, partial, message, expected):
        """Make an assertion operation to evaluate later.

        Parameters
        ----------
        partial: function
            The assertion to evaluated.
        message: string
            A message describing the assertion.
        expected: primitive
            The operand for the expression. There may be none.
        """
        def assertion():
            passed = bool(int(self.negated) ^ int(partial()))
            pass_message = (
                self.override_message_pass
                if self.override_message_pass
                else 'Success'
            )
            fail_message = (
                self.override_message_fail
                if self.override_message_fail
                else 'Failure'
            )
            test_name = (
                self.override_test_name
                if self.override_test_name
                else self._generate_description(message, expected)
            )
            student_output = (
                self.override_student_output
                if self.override_student_output
                else self.actual
            )
            result = {
                # "True" and "False" need to be strings, otherwise they
                # are lowercased when stringified by JS and cause parse errors.
                'success': "True" if passed else "False",
                'test': test_name,
                'solutionOutput': self.override_solution_output,
                'studentOutput': student_output,
                'message': pass_message if passed else fail_message,
                'showDiff': "True" if self.override_show_diff else "False"
            }
            return result

        self.expectations.append(assertion)
        self.assertion = assertion

        return assertion

    def __partial(self, op, expected):
        """Create a partial.

        Parameters
        ----------
        op: object
            Operator used to compare actual and expected.
        expected: primitive
            Item compared against actual. Can be None.

        Returns function.

        """
        def wrapper():
            try:
                # try to strip whitespace if operands are strings
                return op(self.actual.strip('\n'), expected.strip('\n'))
            except AttributeError:
                # otherwise proceed on non-string operands
                return op(self.actual, expected)

        return wrapper

    def _generate_description(self, message, expected):
        """Create an understandable description for the test.

        Parameters
        ----------
        message: string
            A string describing the expectation.
        expected: primitive
            A primitive that was used in the comparison.

        Returns a string.

        """
        description = "Expected {} {}".format(json.dumps(self.actual), message)

        description += " {}".format(json.dumps(expected))

        return description

    def to_be(self, expected):
        """Create expectation that self.actual == expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.is_, expected),
                              'to be',
                              expected)
        return self

    def not_to_be(self, expected):
        """Create expectation that self.actual != expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.negated = True
        self.__make_assertion(self.__partial(operator.is_, expected),
                              'not to be',
                              expected)
        return self

    def to_be_greater_than(self, expected):
        """Create expectation that self.actual > expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.gt, expected),
                              'to be greater than',
                              expected)
        return self

    def to_be_greater_than_or_equal_to(self, expected):
        """Create expectation that self.actual >= expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.ge, expected),
                              'to be greater than or equal to',
                              expected)
        return self

    def to_be_less_than(self, expected):
        """Create expectation that self.actual < expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.lt, expected),
                              'to be less than',
                              expected)
        return self

    def to_be_less_than_or_equal_to(self, expected):
        """Create expectation that self.actual <= expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.le, expected),
                              'to be less than or equal to',
                              expected)
        return self

    def to_contain(self, expected):
        """Create expectation that self.actual contains expected.

        Parameters
        ----------
        expected: primitive
            The primitive to search for in self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(operator.contains, expected),
                              'to contain',
                              expected)
        return self

    def not_to_contain(self, expected):
        """Create expectation that self.actual does not contain expected.

        Parameters
        ----------
        expected: primitive
            The primitive to search for in self.actual.

        Returns an expect object.

        """
        self.negated = True
        self.__make_assertion(self.__partial(operator.contains, expected),
                              'not to contain',
                              expected)
        return self

    def to_contain_line(self, expected):
        """Create expectation that a line in self.actual contains expected.
        Parameters
        ----------
        expected: primitive
            The primitive to search for in self.actual.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(line_contains, expected),
                              'to contain line',
                              expected)
        return self

    def not_to_contain_line(self, expected):
        """Create expectation that a line self.actual doesn't contain expected.

        Parameters
        ----------
        expected: primitive
            The primitive to search for in self.actual.

        Returns an expect object.

        """
        self.negated = True
        self.__make_assertion(self.__partial(line_contains, expected),
                              'not to contain line',
                              expected)
        return self

    def to_equal(self, expected):
        """Create expectation that self.actual is equal to expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.
        """
        self.__make_assertion(self.__partial(operator.eq, expected),
                              'to equal',
                              expected)
        return self

    def not_to_equal(self, expected):
        """Create expectation that self.actual is not equal to expected.

        Parameters
        ----------
        expected: primitive
            The primitive to compare with self.actual.

        Returns an expect object.
        """
        self.negated = True
        self.__make_assertion(self.__partial(operator.eq, expected),
                              'not to equal',
                              expected)
        return self

    def to_be_truthy(self):
        """Create expectation that self.actual is Truthy.

        Returns an expect object.

        """
        self.__make_assertion(self.__partial(lambda actual, _: bool(actual), None),
                              'to be',
                              'truthy')
        return self

    def to_be_falsey(self):
        """Create expectation that self.actual is Falsey.

        Returns an expect object.

        """
        self.negated = True
        self.__make_assertion(self.__partial(lambda actual, _: bool(actual), None),
                              'to be',
                              'falsey')
        return self

    def with_options(self, message_pass='',
                     message_fail='', test_name='', show_diff=False,
                     solution_output='', student_output=''):
        """Pass options to override test results.

        Parameters
        ----------
        message_pass: string
            A message to print on passing.
        message_fail: string
            A message to print on failing.
        test_name: string
            The name of the test.
        show_diff: boolean
            Whether or not to show the diff in the results.
        solution_output: string
            A solution output to be shown in the reuslts.

        """
        self.override_message_pass = message_pass if message_pass else self.override_message_pass
        self.override_message_fail = message_fail if message_fail else self.override_message_fail
        self.override_test_name = test_name if test_name else self.override_test_name
        self.override_show_diff = show_diff if show_diff else self.override_show_diff
        # TODO -- change api.
        self.override_solution_output = solution_output if solution_output else self.override_solution_output
        self.override_student_output = student_output if student_output else self.override_student_output

        return self

    ########################################################
    ## Below are assertions for Turtle Python.
    ########################################################

    def to_contain_command(self, expected):
        """Create expectation that self.actual contains the command `expected`.

        Returns an expect object.

        """
        self.override_test_name = 'Expected your commands to contain {}.'.format(expected)
        self.__make_assertion(self.__partial(contains_command, expected),
                              'to contain command',
                              expected)
        return self

def line_contains(lhs, rhs):
    """An operator to check if a line in lhs string contains rhs.

    Parameters
    ----------
    lhs: string
        The left hand side of the operation.
    rhs: string
        The right hand side of the operation.

    Returns boolean.

    """
    lines = lhs.split('\n')
    return rhs in lines

def _flush_expectations():
    """Flushes expectations.

    Returns a list.

    """
    flushed_expectations = expect.expectations
    expect.expectations = []
    return flushed_expectations


def contains_command(lhs, rhs):
    """An operator to check if a list of commands (lhs) contains command (rhs).

    Parameters
    ----------
    lhs: list
        The left hand side of the operation, a list of commands.
        Their format is [('command_name', (arg1, arg2)), ...].
    rhs: string
        The right hand side of the operation, a string of the comand that
        should bein the lhs. 'forward', 'backward', etc.

    Returns boolean.

    """
    return any([(command[0] == rhs) for command in lhs])


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class PythonTestSuite(object):
    """A test suite object, from which test suites are inherited."""

    suites = []

    def __init__(self):
        PythonTestSuite.suites += [self]

    def before_run(*args):
        pass

    def after_run(*args):
        pass

def strip_comments(text):
    """Naively removes comments from a string.

    Parameters
    ----------
    text: string
        String of code to remove comments from.

    Returns string.

    """
    quote_chars = ["'", '"']
    result = []
    for line in text.split('\n'):
        try:
            # find index of comment character
            delim_index = line.index('#')
        except ValueError:
            # no comment character
            result.append(line)
        else:
            # side of string before comment
            left_side = line[:delim_index]
            # extract all quote characters from left_side
            quotes = ''.join([ch for ch in left_side if ch in quote_chars])
            quote_stack = []
            for quote in quotes:
                # if it's a matching quote, a string is closed
                if quote_stack and quote_stack[len(quote_stack) - 1] == quote:
                    quote_stack.pop()
                # otherwise, push it on
                else:
                    quote_stack.append(quote)
            # if the quote stack is empty, then the # is outside a string
            if quote_stack == []:
                result.append(left_side)
            # otherwise the # is within a string, append the entire line
            else:
                result.append(line)
    return '\n'.join(result)

class TestSuite(PythonTestSuite):
    # Any values that should be passed to any call to `input`
    inputs = []

    # Write any tests that should run before the code is evaluated
    def before_run(self, student_code, solution_code):
        expect(student_code).to_contain('if').with_options(
            test_name='Your code should use an if statement.',
            message_fail='When should I dance in the rain?'
        )
        expect(student_code).to_contain('else:').with_options(
            test_name='Your code should use an else statement.',
            message_fail='When should I dance in the sun?',
        )
        no_spaces = student_code.replace(' ','')

        if "==True" in no_spaces or "==False" in no_spaces:
            if "==True" in no_spaces: 
                output = "== True" 
            else: 
                output = "== False"
            expect("Failed").to_be("Passed").with_options(
                test_name="You should not compare Boolean variables with True or False",
                solution_output="if is_raining:",
                student_output=output
                )


    # Write any tests that should run after the code is evaluated
    def after_run(self, student_code, solution_code, student_output, solution_output):
        # Figure out if boolean is T or F
        no_spaces = student_code.replace(' ','')
        if "=True" in no_spaces:
            expect(student_output).to_contain("rain").with_options(
                test_name="If the Boolean variable is True, you should dance in the rain")
        elif "=False" in no_spaces:
            expect(student_output).to_contain("sun").with_options(
                test_name="If the Boolean variable is False, you should dance in the sun")
        else:
            expect(True).to_be(False).with_options(
                test_name="You should define a Boolean variable",
                student_output=student_code)




TestSuite()


student_code = open('studentcode.py').read()
solution_code = open('solutioncode.py').read()

__private_context = []

for e in _flush_expectations():
    result = e()
    __private_context.append(result)

for i, suite in enumerate(PythonTestSuite.suites):
    results = {}
    # BEFORE RUN
    # modifications is either None or an object with keys
    # student_code, solution_code, and inputs
    modifications = suite.before_run(student_code, solution_code)
    try:
        student_code = modifications['student_code']
        solution_code = modifications['solution_code']
        suite.inputs.extend(modifications['inputs'])
    except:
        pass

    before_run_test_results = []
    for e in _flush_expectations():
        result = e()
        before_run_test_results.append(result)

    __private_context.append(before_run_test_results)

    # EVALUATE
    inputs = suite.inputs
    current_input = 0
    with stdoutIO() as _s:
        try:
            exec(student_code)
        except:
            print("Something wrong with the code")
    student_output = _s.getvalue()
    # EVALUATE
    inputs = suite.inputs
    current_input = 0
    with stdoutIO() as ss:
        try:
            exec(solution_code)
        except:
            print("Something wrong with the code")
    solution_output = ss.getvalue()

    # AFTER RUN
    suite.after_run(student_code, solution_code, student_output, solution_output)
    after_run_test_results = []
    for e in _flush_expectations():
        result = e()
        after_run_test_results.append(result)

    __private_context.append(after_run_test_results)

    __private_context.append(results)

print(json.dumps(__private_context))
