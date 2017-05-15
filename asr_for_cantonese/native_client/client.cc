#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include <string.h>
#include <sox.h>
#include <time.h>
#include "deepspeech.h"
#ifdef __APPLE__
#include <unistd.h>
#endif

#define N_CEP 26
#define N_CONTEXT 9

struct ds_result {
  char* string;
  double cpu_time_overall;
  double cpu_time_mfcc;
  double cpu_time_infer;
};

// DsSTT() instrumented
struct ds_result*
LocalDsSTT(DeepSpeech& aCtx, const short* aBuffer, size_t aBufferSize,
           int aSampleRate)
{
  float* mfcc;
  struct ds_result* res = (struct ds_result*)malloc(sizeof(struct ds_result));
  if (!res) {
    return NULL;
  }

  clock_t ds_start_time = clock();
  clock_t ds_end_mfcc = 0, ds_end_infer = 0;

  int n_frames = 0;
  aCtx.getMfccFrames(aBuffer, aBufferSize, aSampleRate, &mfcc, &n_frames);
  ds_end_mfcc = clock();

  res->string = aCtx.infer(mfcc, n_frames);
  ds_end_infer = clock();

  free(mfcc);

  res->cpu_time_overall =
    ((double) (ds_end_infer - ds_start_time)) / CLOCKS_PER_SEC;
  res->cpu_time_mfcc =
    ((double) (ds_end_mfcc  - ds_start_time)) / CLOCKS_PER_SEC;
  res->cpu_time_infer =
    ((double) (ds_end_infer - ds_end_mfcc))   / CLOCKS_PER_SEC;

  return res;
}

int
main(int argc, char **argv)
{
  if (argc < 3 || argc > 4) {
    printf("Usage: deepspeech MODEL_PATH AUDIO_PATH [-t]\n");
    printf("  MODEL_PATH\tPath to the model (protocol buffer binary file)\n");
    printf("  AUDIO_PATH\tPath to the audio file to run"
           " (any file format supported by libsox)\n");
    printf("  -t\t\tRun in benchmark mode, output mfcc & inference time\n");
    return 1;
  }

  // Initialise DeepSpeech
  DeepSpeech ctx = DeepSpeech(argv[1], N_CEP, N_CONTEXT);

  // Initialise SOX
  assert(sox_init() == SOX_SUCCESS);

  sox_format_t* input = sox_open_read(argv[2], NULL, NULL, NULL);
  assert(input);

  int sampleRate = (int)input->signal.rate;

  // Resample/reformat the audio so we can pass it through the MFCC functions
  sox_signalinfo_t target_signal = {
      SOX_UNSPEC, // Rate
      1, // Channels
      16, // Precision
      SOX_UNSPEC, // Length
      NULL // Effects headroom multiplier
  };

  sox_encodinginfo_t target_encoding = {
    SOX_ENCODING_SIGN2, // Sample format
    16, // Bits per sample
    0.0, // Compression factor
    sox_option_default, // Should bytes be reversed
    sox_option_default, // Should nibbles be reversed
    sox_option_default, // Should bits be reversed (pairs of bits?)
    sox_false // Reverse endianness
  };

#ifdef __APPLE__
  // It would be preferable to use sox_open_memstream_write here, but OS-X
  // doesn't support POSIX 2008, which it requires. See Issue #461.
  // Instead, we write to a temporary file.
  char* output_name = tmpnam(NULL);
  assert(output_name);
  sox_format_t* output = sox_open_write(output_name, &target_signal,
                                        &target_encoding, "raw", NULL, NULL);
#else
  char* buffer;
  size_t buffer_size;
  sox_format_t* output = sox_open_memstream_write(&buffer, &buffer_size,
                                                  &target_signal,
                                                  &target_encoding,
                                                  "raw", NULL);
#endif

  assert(output);

  // Setup the effects chain to decode/resample
  char* sox_args[10];
  sox_effects_chain_t* chain =
    sox_create_effects_chain(&input->encoding, &output->encoding);

  sox_effect_t* e = sox_create_effect(sox_find_effect("input"));
  sox_args[0] = (char*)input;
  assert(sox_effect_options(e, 1, sox_args) == SOX_SUCCESS);
  assert(sox_add_effect(chain, e, &input->signal, &input->signal) ==
         SOX_SUCCESS);
  free(e);

  e = sox_create_effect(sox_find_effect("channels"));
  assert(sox_effect_options(e, 0, NULL) == SOX_SUCCESS);
  assert(sox_add_effect(chain, e, &input->signal, &output->signal) ==
         SOX_SUCCESS);
  free(e);

  e = sox_create_effect(sox_find_effect("output"));
  sox_args[0] = (char*)output;
  assert(sox_effect_options(e, 1, sox_args) == SOX_SUCCESS);
  assert(sox_add_effect(chain, e, &input->signal, &output->signal) ==
         SOX_SUCCESS);
  free(e);

  // Finally run the effects chain
  sox_flow_effects(chain, NULL, NULL);
  sox_delete_effects_chain(chain);

  // Close sox handles
  sox_close(output);
  sox_close(input);

#ifdef __APPLE__
  size_t buffer_size = (size_t)(output->olength * 2);
  char* buffer = (char*)malloc(sizeof(char) * buffer_size);
  FILE* output_file = fopen(output_name, "rb");
  assert(fread(buffer, sizeof(char), buffer_size, output_file) == buffer_size);
  fclose(output_file);
  unlink(output_name);
#endif

  // Pass audio to DeepSpeech
  struct ds_result* result = LocalDsSTT(ctx, (const short*)buffer, buffer_size / 2, sampleRate);
  free(buffer);

  if (result) {
    if (result->string) {
      printf("%s\n", result->string);
      free(result->string);
    }

    if ((argc == 4) && (strncmp(argv[3], "-t", 3) == 0)) {
      printf("cpu_time_overall=%.05f cpu_time_mfcc=%.05f cpu_time_infer=%.05f\n",
             result->cpu_time_overall,
             result->cpu_time_mfcc,
             result->cpu_time_infer);
    }

    free(result);
  }

  // Deinitialise and quit
  sox_quit();

  return 0;
}
