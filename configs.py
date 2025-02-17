import random
import torch
import logging
import numpy as np
import multiprocessing

logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument("--task", type=str, required=True,
                        choices=['summarize', 'translate', 'refine', 'generate', 'defect', 'clone'])# without complete
    parser.add_argument("--sub_task", type=str, default='')
    parser.add_argument("--add_lang_ids", action='store_true')
    # plbart unfinished
    parser.add_argument("--model_name", default="roberta",
                        type=str, choices=['roberta', 'codebert', 'graphcodebert', 'bart', 'plbart', 't5', 'codet5','unixcoder'])
    parser.add_argument('--seed', type=int, default=1234,
                        help="random seed for initialization")  # previous one 42
    parser.add_argument("--local_rank", type=int, default=-1,
                        help="For distributed training: local_rank")
    parser.add_argument("--no_cuda", action='store_true',
                        help="Avoid using CUDA when available")
    parser.add_argument('--huggingface_locals', type=str, default='data/huggingface_locals',
                    help="directory to save huggingface models")
    parser.add_argument("--cache_path", type=str, default='cache_data')
    parser.add_argument("--res_dir", type=str, default='results',
                        help='directory to save fine-tuning results')
    parser.add_argument("--res_fn", type=str, default='')
    # parser.add_argument("--model_dir", type=str, default='saved_models',
    #                     help='directory to save fine-tuned models')
    parser.add_argument("--summary_dir", type=str, default='tensorboard',
                        help='directory to save tensorboard summary')
    parser.add_argument("--data_num", type=int, default=-1,
                        help='number of data instances to use, -1 for full data')
    # parser.add_argument("--gpu", type=int, default=0,
    #                     help='index of the gpu to use in a cluster')
    parser.add_argument("--data_dir", default='data', type=str)
    parser.add_argument("--output_dir", default='outputs', type=str,
                        help="The output directory where the model predictions and checkpoints will be written.")
    parser.add_argument("--do_train", action='store_true',
                        help="Whether to run eval on the train set.")
    parser.add_argument("--do_eval", action='store_true',
                        help="Whether to run eval on the dev set.")
    parser.add_argument("--do_test", action='store_true',
                        help="Whether to run eval on the test set.")
    parser.add_argument("--add_task_prefix", action='store_true',
                        help="Whether to add task prefix for t5 and codet5")
    parser.add_argument("--save_last_checkpoints", action='store_true')
    parser.add_argument("--always_save_model", action='store_true')
    parser.add_argument("--do_eval_bleu", action='store_true',
                        help="Whether to evaluate bleu on dev set.")
    parser.add_argument("--start_epoch", default=0, type=int)
    parser.add_argument("--num_train_epochs", default=100, type=int)
    parser.add_argument("--patience", default=5, type=int)
    parser.add_argument('--gradient_accumulation_steps', type=int, default=1,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument("--lr", default=5e-5, type=float,
                        help="The initial learning rate for Adam.")
    parser.add_argument("--beam_size", default=10, type=int,
                        help="beam size for beam search")
    parser.add_argument("--weight_decay", default=0.0, type=float,
                        help="Weight deay if we apply some.")
    parser.add_argument("--adam_epsilon", default=1e-8, type=float,
                        help="Epsilon for Adam optimizer.")
    parser.add_argument("--max_grad_norm", default=1.0, type=float,
                        help="Max gradient norm.")
    parser.add_argument("--warmup_steps", default=100, type=int,
                        help="Linear warmup over warmup_steps.")
    parser.add_argument("--batch_size", default=8, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--dev_batch_size", default=32, type=int,
                        help="Batch size per GPU/CPU for validating.")
    parser.add_argument("--test_batch_size", default=32, type=int,
                        help="Batch size per GPU/CPU for testing.")
    parser.add_argument("--attention_batch_size", default=100, type=int,
                        help="Batch size per GPU/CPU for computing attention.")
    parser.add_argument("--max_source_length", default=320, type=int,
                        help="max_source_length")
    parser.add_argument("--max_target_length", default=150, type=int,
                        help="max_target_length")
    parser.add_argument("--is_clone_sample", default=0, type=int,
                        help="clone&defect data is large, 0 for not sample and 1 for sample")                    
    # parser.add_argument('--layer_num', type=int, default=-1,
    #                 help="layer which attention is concerned, -1 for last layer, else for all 0-11 layers")
    # parser.add_argument('--quantile_threshold', type=float, default=0.75,
    #                 help="threshold of quantile which we concern attention should be gt and distance should be lt")
    # parser.add_argument('--frequent_type',  default=1, type=int, choices=[0,1],
    #                 help="whether only use frequent_type")
    # parser.add_argument('--upgraded_ast',  default=1, type=int, choices=[0,1],
    #                 help="whether to use upgraded ast")
    parser.add_argument('--few_shot',  default=-1, type=int,
                    help="use k shot, -1 for full data")

    parser.add_argument("--prefix_tuning", default=False, type=str,
                    help="parameter-efficient prefix tuning, pass_tuning refers to GAT prefix,\
                    GCN refers to GCN prefix,prefix_tuning refers to MLP prefix",\
                        choices=['pass_tuning','GCN' ,'prefix_tuning', False])
    parser.add_argument("--adapter_tuning", default=0, type=int,
                    help="parameter-efficient adapter tuning, 0 for not tuning, 1 for tuning")#only support codet5 currently
    parser.add_argument("--bitfit", default=0, type=int,
                    help="parameter-efficient bitfit, 0 for not tuning, 1 for tuning")
    

    parser.add_argument("--old_prefix_dir", default='old_data_prefix', type=str,
                        help="directory to score graphmetadata.txt")
    parser.add_argument("--prefix_dir", default='data_prefix', type=str,
                        help="directory to score graphmetadata.txt")
    parser.add_argument("--prefix_token_level", default='token', type=str,
                        help="how to parse initial prefix code, choose 'token' or 'subtoken' level of ids/init_dist_weight")
    parser.add_argument("--gat_token_num", default=32, type=int,
                        help="number of tokens to use for gat, must be divided with max_source_length in encoder2decoder with no remainder")
    parser.add_argument("--fix_model_param", default=1, type=int,
                    help="when prefix_tuning, fix model param or not ")
    
    parser.add_argument("--knowledge_usage", default='separate', type=str,
                        help="for t5&bart, how knowledge prefix use: separate or concatenate",choices=['separate','concatenate'])
    parser.add_argument("--use_description", default=0, type=int,
                    help="use_description or not ")
    parser.add_argument("--concatenate_description", default=0, type=int,
                    help="concatenate_description or not ")
    parser.add_argument("--map_description", default=0, type=int,
                    help="map_description or not ")
    parser.add_argument("--prefix_dropout", default=0.0, type=float,
                        help="prefix_dropout.")
    parser.add_argument("--retriever_mode", default='retrieve', type=str,
                        help="how to retrieve code piece to init GAT, choose from random or retrieve",
                        choices=['random', 'retrieve','old'])
    parser.add_argument("--adjcency_mode", default='sast', type=str,
                    help="how code distance matrix input as GAT adjcency matrix",choices=['fully-connected','sast'])
    args = parser.parse_args()
    return args


def set_dist(args):
    # Setup CUDA, GPU & distributed training
    if args.local_rank == -1 or args.no_cuda:
        device = torch.device(
            "cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
        args.n_gpu = torch.cuda.device_count()
    else:
        # Setup for distributed data parallel
        torch.cuda.set_device(args.local_rank)
        device = torch.device("cuda", args.local_rank)
        torch.distributed.init_process_group(backend='nccl')
        args.n_gpu = 1
    cpu_count = multiprocessing.cpu_count()
    logger.warning("Process rank: %s, device: %s, n_gpu: %s, distributed training: %s, cpu count: %d",
                   args.local_rank, device, args.n_gpu, bool(args.local_rank != -1), cpu_count)
    args.device = device
    args.cpu_count = cpu_count


def set_seed(args):
    """set random seed."""
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if args.n_gpu > 0:
        torch.cuda.manual_seed_all(args.seed)


def set_hyperparas(args):
    pass