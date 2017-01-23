import os
import sys
from optparse import OptionParser, OptionGroup
from collections import OrderedDict

from pyrocko.fomosto_report import GreensFunctionTest as gftest
from pyrocko.fomosto_report import FilterFrequencyError as gft_ffe

spstr = '\n' + ' '*20
subcmds_desc = OrderedDict([
        ('single',          'create pdf of a single store'),
        ('double',          'create pdf of two stores'),
        ('sstandard',       'create a single store pdf with standard setup'),
        ('dstandard',       'create a double store pdf with standard setup'),
        ('slow',            'create a single store pdf, filtering the' +
                            spstr + 'traces with a low frequency'),
        ('dlow',            'create a double store pdf, filtering the' +
                            spstr + 'traces with a low frequency'),
        ('shigh',           'create a single store pdf, filtering the' +
                            spstr + 'traces with a low frequency'),
        ('dhigh',           'create a single store pdf, filtering the' +
                            spstr + 'traces with a low frequency'),
        ('slowband',        'create a single store pdf with a low' +
                            spstr + 'frequency band filter'),
        ('dlowband',        'create a double store pdf with a low' +
                            spstr + 'frequency band filter'),
        ('shighband',       'create a single store pdf with a high' +
                            spstr + 'frequency band filter'),
        ('dhighband',       'create a double store pdf with a high' +
                            spstr + 'frequency band filter'),
        ('snone',           'create a single store pdf with unfiltered'
                            ' traces'),
        ('dnone',           'create a double store pdf with unfiltered'
                            ' traces')])

subcmds_uses = {
        'single':           'single <input config file> [options]',
        'double':           'double <input config file> [options]',
        'sstandard':        'sstandard  <store dir> <store id> [options]',
        'dstandard':        'dstandard <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]',
        'slow':             'slow  <store dir> <store id> [options]',
        'dlow':             'dlow <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]',
        'slowband':         'slowband  <store dir> <store id> [options]',
        'dlowband':         'dlowband <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]',
        'shighband':        'shighband  <store dir> <store id> [options]',
        'dhighband':        'dhighband <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]',
        'shigh':            'shigh <store dir> <store id> [options]',
        'dhigh':            'dhigh <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]',
        'snone':            'snone <store dir> <store id> [options]',
        'dnone':            'dnone <store dir> <store id1> <store id2>'
                            ' <sensor distance minimum>'
                            ' <sensor distance maximum> [options]'}


def dict_to_string(dic):
    st = 4
    st2 = 20
    s = ''
    for k, v in dic.iteritems():
        s += '\n{0}{1}{2}{3}'.format(' '*st, k, ' '*(st2 - st - len(k)), v)
    return s


def add_common_options(parser):
    parser.add_option('--show_defaults', '-d', action='store_false',
                      help='Show the default values of command options.'
                           ' Must be typed before help option.')
    parser.add_option('--plot_velocity', '-v', action='store_true',
                      help='Plot the velocity traces also.', default=False)
    parser.add_option('--pdf_dir', '-p',
                      help='The directory where the pdf will be saved to.'
                           ' Default is the HOME directory.',
                      default=None)
    parser.add_option('--output', '-o',
                      help='The full path and name to save the'
                      ' resulting configuration file.',
                      default=None)
    parser.add_option('--report_only', '-r', dest='plot_everything',
                      action='store_false', default=True,
                      help='Do not plot the trace graphs')


def add_sensor_options(parser):
    grp = OptionGroup(parser, 'Seismic sensor distance options')
    grp.add_option('--distance_min', '-n', type=float, default=None,
                   help="The minimum distance to place sensors. Value of"
                        " 'None' will use store minimum.")
    grp.add_option('--distance_max', '-x', type=float, default=None,
                   help="The maximum distance to place sensors. Value of"
                        " 'None' will use store maximum.")
    grp.add_option('--sensor_count', '-c', type=int, default=50,
                   help="The number of sensors to use.")
    parser.add_option_group(grp)


def add_source_options(parser):
    grp = OptionGroup(parser, 'Seismic source options')
    grp.add_option('--depth',
                   dest='source_depth',
                   type=float,
                   help="The depth of the source. Value of 'None' will place"
                        " source at middle depth of allowed values.",
                   default=None)
    parser.add_option_group(grp)


def add_filter_options(parser):
    grp = OptionGroup(parser, 'Trace frequency filter options')
    grp.add_option('--lowpass',
                   dest='lowpass_frequency',
                   type=float,
                   help='The value of the lowpass filter applied to traces.',
                   default=None)
    grp.add_option('--lowpass_rel',
                   dest='rel_lowpass_frequency',
                   type=float,
                   help='''The percentage of the store's sampling rate'''
                        ' to be used as the lowpass filter.',
                   default=None)
    grp.add_option('--highpass',
                   dest='highpass_frequency',
                   type=float,
                   help='The value of the highpass filter applied to traces.',
                   default=None)
    grp.add_option('--highpass_rel',
                   dest='rel_highpass_frequency',
                   type=float,
                   help='''The percentage of the store's samping rate'''
                        ' to be used as the lowpass filter.',
                   default=None)
    parser.add_option_group(grp)


def add_double_options(parser):
    grp = OptionGroup(parser, 'Double store plotting options')
    grp.add_option('--together', '-t', dest='together',
                   action='store_true', default=True,
                   help='Plot both stores on same axes.')
    grp.add_option('--separate', '-s', dest='together',
                   action='store_false',
                   help='Plot stores next to each other.')
    parser.add_option_group(grp)


def cl_parse(command, args, setup=None):
    usage = '{0} {1}'.format(program_name, subcmds_uses[command])
    desc = ' '.join(subcmds_desc[command].split())
    parser = OptionParser(usage=usage, description=desc)
    add_common_options(parser)
    if setup:
        setup(parser)

    if args and args[0] in ('-d', '--show_defaults'):
        for opt in parser.option_list:
            if opt.default == ('NO', 'DEFAULT'):
                continue
            opt.help += (' ' if opt.help else '') + '[default: %default]'
        for grp in parser.option_groups:
            for opt in grp.option_list:
                if opt.default == ('NO', 'DEFAULT'):
                    continue
                opt.help += (' ' if opt.help else '') + '[default: %default]'
    opts, args = parser.parse_args(args)
    opts = vars(opts)
    if 'show_defaults' in opts:
        del opts['show_defaults']
    return parser, opts, args


def verify_arguements(command, allowed, args):
    if len(args) != allowed:
        raise TypeError('{0}() takes {1} arguements ({2} given)'.format(
            command, allowed, len(args)))

    st_dir = args.pop(0)
    if not os.path.exists(st_dir):
        raise OSError('Path does not exist: {0}'.format(st_dir))

    if allowed == 1:
        return st_dir

    if st_dir[-1] != '/':
        st_dir += '/'
    st_id = args.pop(0)
    if not os.path.exists(st_dir + st_id):
        raise OSError('Store does not exist: {0}'.format(st_id))

    if args:
        st_id2 = args.pop(0)
        if not os.path.exists(st_dir + st_id2):
            raise OSError('Store does not exist: {0}'.format(st_id2))
        sen_min = float(args.pop(0))
        sen_max = float(args.pop(0))
        return st_dir, st_id, st_id2, sen_min, sen_max
    else:
        return st_dir, st_id


def verify_options(command, **opts):
    lpf = None
    hpf = None
    rlpf = None
    rhpf = None

    tstr = 'lowpass_frequency'
    if tstr in opts:
        lpf = opts[tstr]
    tstr = 'highpass_frequency'
    if tstr in opts:
        hpf = opts[tstr]
    tstr = 'rel_lowpass_frequency'
    if tstr in opts:
        rlpf = opts[tstr]
    tstr = 'rel_highpass_frequency'
    if tstr in opts:
        rhpf = opts[tstr]

    if lpf and rlpf:
        raise gft_ffe('lowpass')
    if hpf and rhpf:
        raise gft_ffe('highpass')


def command_single(command, args):
    def setup(parser):
        parser.set_defaults(plot_velocity=None)
        parser.set_defaults(plot_everything=None)

    parser, opts, args = cl_parse(command, args, setup)
    filename = verify_arguements('single', 1, args)
    out_filename = opts.pop('output')
    gft = gftest.createPdfFromFile(filename, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_sstandard(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)

    parser, opts, args = cl_parse(command, args, setup)
    st_dir, st_id = verify_arguements('sstandard', 2, args)
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_slow(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)
        parser.add_option('--lowpass_rel',
                          dest='rel_lowpass_frequency',
                          type=float,
                          help='''The percentage of the store's sampling'''
                               ' rate to be used as the lowpass filter.',
                          default=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    st_dir, st_id = verify_arguements('slow', 2, args)
    opts['rel_highpass_frequency'] = None
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_shigh(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)
        parser.add_option('--highpass_rel',
                          dest='rel_highpass_frequency',
                          type=float,
                          help='''The percentage of the store's sampling'''
                               ' rate to be used as the highpass filter.',
                          default=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    st_dir, st_id = verify_arguements('shigh', 2, args)
    opts['rel_lowpass_frequency'] = None
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_slowband(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)
        add_filter_options(parser)
        parser.set_defaults(lowpass_frequency=0.0018)
        parser.set_defaults(highpass_frequency=0.004)

    parser, opts, args = cl_parse(command, args, setup=setup)
    st_dir, st_id = verify_arguements('slowband', 2, args)
    verify_options('slowband', **opts)
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_shighband(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)
        add_filter_options(parser)
        parser.set_defaults(rel_lowpass_frequency=0.125)
        parser.set_defaults(rel_highpass_frequency=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    st_dir, st_id = verify_arguements('shighband', 2, args)
    verify_options('shighband', **opts)
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_snone(command, args):
    def setup(parser):
        add_source_options(parser)
        add_sensor_options(parser)

    parser, opts, args = cl_parse(command, args, setup=setup)
    st_dir, st_id = verify_arguements('snone', 2, args)
    opts['rel_lowpass_frequency'] = None
    opts['rel_highpass_frequency'] = None
    out_filename = opts.pop('output')
    gft = gftest.runStandardCheck(st_dir, st_id, **opts)
    if out_filename is not None:
        return gft, out_filename


def command_double(command, args):
    def setup(parser):
        add_double_options(parser)
        parser.set_defaults(plot_velocity=None)
        parser.set_defaults(plot_everything=None)

    parser, opts, args = cl_parse(command, args, setup=setup)
    filename = verify_arguements('double', 1, args)
    verify_options('double', **opts)
    out_filename = opts.pop('output')
    gfts = gftest.createPdfFromFile(filename, 2, **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dstandard(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dstandard', 5, args)
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dlow(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)
        parser.add_option('--lowpass_rel',
                          dest='rel_lowpass_frequency',
                          type=float,
                          help='''The percentage of the store's sampling'''
                               ' rate to be used as the lowpass filter.',
                          default=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dlow', 5, args)
    opts['rel_highpass_frequency'] = None
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dhigh(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)
        parser.add_option('--highpass_rel',
                          dest='rel_highpass_frequency',
                          type=float,
                          help='''The percentage of the store's sampling'''
                               ' rate to be used as the highpass filter.',
                          default=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dhigh', 5, args)
    opts['rel_lowpass_frequency'] = None
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dlowband(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)
        add_filter_options(parser)
        parser.set_defaults(lowpass_frequency=0.0018)
        parser.set_defaults(highpass_frequency=0.004)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dlowband', 5, args)
    verify_options('dlowband', **opts)
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dhighband(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)
        add_filter_options(parser)
        parser.set_defaults(rel_lowpass_frequency=0.125)
        parser.set_defaults(rel_highpass_frequency=0.25)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dhighband', 5, args)
    verify_options('dhighband', **opts)
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


def command_dnone(command, args):
    def setup(parser):
        add_source_options(parser)
        add_double_options(parser)

    parser, opts, args = cl_parse(command, args, setup=setup)
    dir, id1, id2, smin, smax = verify_arguements('dnone', 5, args)
    opts['rel_lowpass_frequency'] = None
    opts['rel_highpass_frequency'] = None
    out_filename = opts.pop('output')
    gfts = gftest.runComparissonStandardCheck(dir, id1, id2, smin, smax,
                                              **opts)
    if out_filename is not None:
        return gfts, out_filename


program_name = 'fomosto report'
usage = 'Create a pdf of displacment and velocity traces, max. amplitude of' \
        ' traces and' \
        ' displacment spectra for Green\'s Function stores.\n\n' \
        'Usage: {0} <subcommand> <arguments> ... [options]\n\nSubcommands:\n' \
        '{1}\n\nTo get further help and a list of available options for any' \
        ' subcommand run:\n\n{2}{0} <subcommand> --help\n\n'. \
        format(program_name, dict_to_string(subcmds_desc), ' '*4)


def run_program(args):
    if len(args) < 1:
        sys.exit(usage)

    command = args.pop(0)
    if command in ('--help', '-h', 'help'):
        sys.exit(usage)

    if command in ('--multiple', '-m'):
        glbs = globals()
        cmds = []
        while args and args[0] in subcmds_desc:
            cmds.append(args.pop(0))
        for command in cmds:
            glbs['command_' + command](args)
        sys.exit()

    if command not in subcmds_desc:
        sys.exit('{0}: error: no such subcommand: {1}'.
                 format(program_name, command))

    if len(args) == 0 or (len(args) == 1 and
                          args[0] in ('-d', '--show_defaults')):
        args.append('--help')
    lst = globals()['command_' + command](command, args)
    if lst is not None:
        gfts = lst[0]
        with open(lst[-1], 'w') as f:
            if isinstance(gfts, gftest):
                f.write(gfts.dump())
            else:
                for i in lst[0]:
                    f.write(i.dump())


if __name__ == '__main__':
    run_program(sys.argv)