WORKDIR="/root/autodl-tmp/HugCode"
HUGGINGFACE_LOCALS="/root/autodl-tmp/HugCode/data/huggingface_models/"
export PYTHONPATH=$WORKDIR

#3090
CUDA=7
BATCH_SIZE=16
DEV_BATCH_SIZE=16
TEST_BATCH_SIZE=16
NUM_TRAIN_EPOCHS=120
LR=5e-4
PATIENCE=120000

# PREFIX_TUNING='pass_tuning'/'GCN'
# PREFIX_DROPOUT=0.0
# PREFIX_TOKEN_LEVEL='token'/'subtoken'
# GAT_TOKEN_NUM=32/64
# ADJCENCY_MODE='sast'/'fully-connected'
# RETRIEVER_MODE='retrieve'/'random'

# #a100
# CUDA=2
# BATCH_SIZE=32
# DEV_BATCH_SIZE=32
# TEST_BATCH_SIZE=32
# NUM_TRAIN_EPOCHS=120
# LR=5e-4
# PATIENCE=120000

MODEL_NAME='graphcodebert'
#codebert
TASK='defect'
#summarize
# SUB_TASK='none'
#python


DATA_NUM=-1
MODEL_DIR=save_models
SUMMARY_DIR=tensorboard
FULL_MODEL_TAG=${MODEL_NAME}


OUTPUT_DIR=${MODEL_DIR}/${TASK}/${FULL_MODEL_TAG}
RES_DIR=results/${TASK}/${FULL_MODEL_TAG}
RES_FN=results/${TASK}/${FULL_MODEL_TAG}.txt

CACHE_DIR=${WORKDIR}/.cache/${TASK}/${FULL_MODEL_TAG}
LOG=${OUTPUT_DIR}/train.log
mkdir -p ${OUTPUT_DIR}
mkdir -p ${CACHE_DIR}
mkdir -p ${RES_DIR}

RUN_FN=${WORKDIR}/main.py

CUDA_VISIBLE_DEVICES=${CUDA} \
TOKENIZERS_PARALLELISM=false \
python ${RUN_FN} ${MULTI_TASK_AUG} \
--do_train \
--do_eval \
--do_eval_bleu \
--do_test \
--save_last_checkpoints \
--always_save_model \
--seed 1234 \
\
--model_name ${MODEL_NAME} \
--task ${TASK} \
--data_num ${DATA_NUM} \
--few_shot -1 \
--output_dir ${OUTPUT_DIR} \
--summary_dir ${SUMMARY_DIR} \
--huggingface_locals ${HUGGINGFACE_LOCALS} \
--data_dir ${WORKDIR}/data \
--cache_path ${CACHE_DIR} \
--res_dir ${RES_DIR} \
--res_fn ${RES_FN} \
\
--batch_size ${BATCH_SIZE} \
--dev_batch_size ${DEV_BATCH_SIZE} \
--test_batch_size ${TEST_BATCH_SIZE} \
--num_train_epochs ${NUM_TRAIN_EPOCHS} \
--lr ${LR} \
--patience ${PATIENCE} \
--warmup_steps 1000 \
--adam_epsilon 1e-08 \
--max_grad_norm 1.0 \
--weight_decay 0.0 \
--start_epoch 0 \
\
--max_source_length 512 \
--max_target_length 3 \
\
--gradient_accumulation_steps 1 \
--local_rank -1 \
\
--prefix_tuning 'pass_tuning' \
--knowledge_usage 'separate' \
--fix_model_param 1 \
--old_prefix_dir ${WORKDIR}/data_prefix \
--prefix_dropout 0.0 \
--prefix_token_level 'token' \
--gat_token_num 32 \
--adjcency_mode 'sast' \
--retriever_mode 'retrieve' \
2>&1 | tee ${LOG}