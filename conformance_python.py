#!/usr/bin/env python3
# Protocol Buffers - Google's data interchange format
# Copyright 2008 Google Inc.  All rights reserved.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""A conformance test implementation for the Python protobuf library.

See conformance.proto for more information.
"""

import betterproto2

import struct
import sys

from lib.conformance import (
    ConformanceResponse,
    ConformanceRequest,
    TestCategory,
    WireFormat,
)
from lib.protobuf_test_messages.proto3 import TestAllTypesProto3


test_count = 0
verbose = False


class ProtocolError(Exception):
    pass


def _create_test_message(type):
    if type == "protobuf_test_messages.proto3.TestAllTypesProto3":
        return TestAllTypesProto3()
    return None


def do_test(request: ConformanceRequest) -> ConformanceResponse:
    response = ConformanceResponse()

    is_json = betterproto2.which_one_of(request, "payload")[0] == "json_payload"
    test_message = _create_test_message(request.message_type)

    if test_message is None:
        return ConformanceResponse(skipped="non proto3 tests not supported")

    if (not is_json) and (test_message is None):
        raise ProtocolError("Protobuf request doesn't have specific payload type")

    try:
        if betterproto2.which_one_of(request, "payload")[0] == "protobuf_payload":
            try:
                test_message.parse(request.protobuf_payload)
            except Exception as e:
                response.parse_error = str(e)
                return response

        elif betterproto2.which_one_of(request, "payload")[0] == "json_payload":
            try:
                ignore_unknown_fields = (  # TODO
                    request.test_category
                    == TestCategory.JSON_IGNORE_UNKNOWN_PARSING_TEST
                )
                test_message.from_json(request.json_payload)
            except Exception as e:
                response.parse_error = str(e)
                return response

        elif betterproto2.which_one_of(request, "payload")[0] == "text_payload":
          return ConformanceResponse(skipped="text input not supported")
          try:
            text_format.Parse(request.text_payload, test_message)
          except Exception as e:
            response.parse_error = str(e)
            return response

        else:
            raise ProtocolError("Request didn't have payload.")

        if request.requested_output_format == WireFormat.UNSPECIFIED:
            raise ProtocolError("Unspecified output format")

        elif request.requested_output_format == WireFormat.PROTOBUF:
            response.protobuf_payload = bytes(test_message)

        elif request.requested_output_format == WireFormat.JSON:
            try:
                response.json_payload = test_message.to_json()
            except Exception as e:
                response.serialize_error = str(e)
                return response

        elif request.requested_output_format == WireFormat.TEXT_FORMAT:
            return ConformanceResponse(skipped="text output not supported")
            # response.text_payload = text_format.MessageToString(
            #     test_message, print_unknown_fields=request.print_unknown_fields
            # )

    except Exception as e:
        response.runtime_error = str(e)

    return response


def do_test_io():
    length_bytes = sys.stdin.buffer.read(4)
    if len(length_bytes) == 0:
        return False  # EOF
    elif len(length_bytes) != 4:
        raise IOError("I/O error")

    length = struct.unpack("<I", length_bytes)[0]
    serialized_request = sys.stdin.buffer.read(length)
    if len(serialized_request) != length:
        raise IOError("I/O error")

    request = ConformanceRequest().parse(serialized_request)

    response = do_test(request)

    serialized_response = bytes(response)
    sys.stdout.buffer.write(struct.pack("<I", len(serialized_response)))
    sys.stdout.buffer.write(serialized_response)
    sys.stdout.buffer.flush()

    # if verbose:
    #   sys.stderr.write(
    #       "conformance_python: request=%s, response=%s\n"
    #       % (
    #           request.ShortDebugString().c_str(),
    #           response.ShortDebugString().c_str(),
    #       )
    #   )

    global test_count
    test_count += 1

    return True


while True:
    if not do_test_io():
        sys.stderr.write(
            "conformance_python: received EOF from test runner "
            + "after %s tests, exiting\n" % (test_count,)
        )
        sys.exit(0)
